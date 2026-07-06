using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CUE4Parse.Encryption.Aes;
using CUE4Parse.FileProvider;
using CUE4Parse.MappingsProvider;
using CUE4Parse.MappingsProvider.Usmap;
using CUE4Parse.UE4.Objects.Core.Misc;
using CUE4Parse.UE4.Versions;
using CUE4Parse_Conversion.Textures.BC;

// Exports 64x64 PNG icons for catalog items straight from the cooked IoStore
// paks, keyed by PersistenceID. Dev-time only tool (not shipped); the app
// works fine with zero icons present (text-tile fallback in ui/icons.py).
//
// Two modes (see README.md):
//   static (default)  - reads each item's own DataAsset export directly from
//                        the paks (ItemIconDiscovery.cs) and follows its real
//                        "Icon" soft-object reference. Works even for items the
//                        in-game dump never saw loaded (IconFile == "").
//   iconlist          - legacy fallback: matches PNG stems named in
//                        iconlist.txt (built from data/item_ids.py's IconFile
//                        field) against texture filenames in the paks.
// static mode always runs the iconlist pass afterwards too, to fill in any
// PIDs it could not resolve (belt and braces) - so "static" is really
// "static, falling back to iconlist for the residue".
class Program
{
    static int Main(string[] args)
    {
        // --find <substring>: list every package path containing the substring
        // (case-insensitive) and exit. Handy for verifying what actually exists
        // in the paks (e.g. all DA_Mount_* assets) without an in-game dump.
        if (args.Length >= 2 && args[0] == "--find")
        {
            var findProvider = new DefaultFileProvider(
                @"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Content\Paks",
                SearchOption.AllDirectories, new VersionContainer(EGame.GAME_UE5_6));
            findProvider.Initialize();
            findProvider.SubmitKey(new FGuid(), new FAesKey("0x0000000000000000000000000000000000000000000000000000000000000000"));
            var needle = args[1].ToLowerInvariant();
            int n = 0;
            foreach (var f in findProvider.Files.Keys.OrderBy(k => k))
                if (f.ToLowerInvariant().Contains(needle)) { Console.WriteLine(f); n++; }
            Console.WriteLine($"[find] {n} matches");
            return 0;
        }

        // args: [paksDir] [usmapPath] [iconlistPath] [outDir] [onlyStem] [mode] [itemsJsonlPath]
        string paks   = args.Length > 0 && !string.IsNullOrEmpty(args[0]) ? args[0] : @"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Content\Paks";
        string usmap  = args.Length > 1 && !string.IsNullOrEmpty(args[1]) ? args[1] : @"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64\ue4ss\Mappings.usmap";
        string list   = args.Length > 2 && !string.IsNullOrEmpty(args[2]) ? args[2] : Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "iconlist.txt");
        string outDir = args.Length > 3 && !string.IsNullOrEmpty(args[3]) ? args[3] : Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "..", "data", "icons");
        string only   = args.Length > 4 && !string.IsNullOrEmpty(args[4]) ? args[4].ToLowerInvariant() : null;
        string mode   = args.Length > 5 && !string.IsNullOrEmpty(args[5]) ? args[5].ToLowerInvariant() : "static";
        string itemsJsonl = args.Length > 6 && !string.IsNullOrEmpty(args[6]) ? args[6]
            : Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "ue4ss_dumper", "ItemDumper_items.jsonl");

        Console.WriteLine($"[cfg] paks={paks}");
        Console.WriteLine($"[cfg] usmap={usmap}");
        Console.WriteLine($"[cfg] iconlist={list}");
        Console.WriteLine($"[cfg] outDir={outDir}");
        Console.WriteLine($"[cfg] mode={mode}");
        if (mode == "static") Console.WriteLine($"[cfg] itemsJsonl={itemsJsonl}");

        // ---- provider setup ----
        EGame egame = EGame.GAME_UE5_6;
        Console.WriteLine($"[cfg] game={egame}");

        var provider = new DefaultFileProvider(paks, SearchOption.AllDirectories, new VersionContainer(egame));
        provider.Initialize();
        // Zero key: works for unencrypted index. If the game encrypts, Files stays 0.
        provider.SubmitKey(new FGuid(), new FAesKey("0x0000000000000000000000000000000000000000000000000000000000000000"));
        provider.MappingsContainer = new FileUsmapTypeMappingsProvider(usmap);

        Console.WriteLine($"[mount] files: {provider.Files.Count}");
        if (provider.Files.Count == 0) { Console.WriteLine("[!] nothing mounted"); return 2; }

        InitDetex();
        Directory.CreateDirectory(outDir);

        // Load the existing manifest first - we only ever add/overwrite, never drop.
        var manifest = LoadExistingManifest(outDir);
        Console.WriteLine($"[merge] existing manifest entries: {manifest.Count}");

        if (mode == "static")
        {
            var result = ItemIconDiscovery.Discover(provider, itemsJsonl, outDir);
            foreach (var kv in result.PidToFile) manifest[kv.Key] = kv.Value;
        }

        // iconlist pass: primary mode when mode=="iconlist"; fallback top-up when mode=="static".
        RunIconlistPass(provider, list, outDir, only, manifest);

        File.WriteAllText(Path.Combine(outDir, "manifest.json"),
            JsonSerializer.Serialize(manifest, new JsonSerializerOptions { WriteIndented = true }));
        Console.WriteLine($"[done] manifest entries: {manifest.Count}");
        return 0;
    }

    // Some icon textures are BC/ASTC/ETC-compressed formats CUE4Parse-Conversion
    // decodes via a managed "Detex" wrapper around a native Detex.dll it embeds
    // as a resource but does not auto-load. Without this, decoding those
    // textures throws "Detex decompression failed: not initialized".
    static void InitDetex()
    {
        try
        {
            var asm = typeof(DetexHelper).Assembly;
            using var s = asm.GetManifestResourceStream("CUE4Parse_Conversion.Resources.Detex.dll");
            if (s == null) { Console.WriteLine("[detex] embedded Detex.dll resource not found; some textures may fail to decode"); return; }
            var tmp = Path.Combine(Path.GetTempPath(), "IconExtractor_Detex.dll");
            using (var fs = File.Create(tmp)) s.CopyTo(fs);
            DetexHelper.Initialize(tmp);
            Console.WriteLine("[detex] initialized");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[detex] init failed ({ex.Message}); some textures may fail to decode");
        }
    }

    static SortedDictionary<string, string> LoadExistingManifest(string outDir)
    {
        var manifest = new SortedDictionary<string, string>();
        var path = Path.Combine(outDir, "manifest.json");
        if (!File.Exists(path)) return manifest;
        try
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            foreach (var prop in doc.RootElement.EnumerateObject())
                manifest[prop.Name] = prop.Value.GetString();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[merge] could not read existing manifest.json ({ex.Message}); starting fresh");
        }
        return manifest;
    }

    // Legacy path: stem ("t_icon_runic_ring") -> list of PersistenceIDs sharing it,
    // built from iconlist.txt (PID<TAB>IconFile, generated from data/item_ids.py by
    // make_iconlist.py). Only fills PIDs not already present in `manifest`.
    static void RunIconlistPass(DefaultFileProvider provider, string list, string outDir, string only,
        SortedDictionary<string, string> manifest)
    {
        if (!File.Exists(list))
        {
            Console.WriteLine($"[iconlist] not found, skipping: {list}");
            return;
        }
        var wanted = new Dictionary<string, List<string>>();
        foreach (var line in File.ReadAllLines(list))
        {
            var parts = line.Split('\t');
            if (parts.Length != 2) continue;
            var pid = parts[0];
            if (manifest.ContainsKey(pid)) continue;   // already resolved (statically or from a prior run)
            var stem = Path.GetFileNameWithoutExtension(parts[1]).ToLowerInvariant();
            if (only != null && stem != only) continue;
            if (!wanted.TryGetValue(stem, out var pids))
                wanted[stem] = pids = new List<string>();
            pids.Add(pid);
        }
        Console.WriteLine($"[iconlist] {wanted.Count} unique icon textures still wanted (after static pass)");
        if (wanted.Count == 0) return;

        int exported = 0, errors = 0;
        foreach (var path in provider.Files.Keys.ToList())
        {
            if (!path.EndsWith(".uasset", StringComparison.OrdinalIgnoreCase)) continue;
            var stem = Path.GetFileNameWithoutExtension(path).ToLowerInvariant();
            if (!wanted.TryGetValue(stem, out var pids)) continue;
            try
            {
                var png = TextureUtil.DecodePackageToPng64(provider, path);
                if (png == null) continue;
                foreach (var pid in pids)
                {
                    var file = pid + ".png";   // PIDs are url-safe base64: filename-safe
                    File.WriteAllBytes(Path.Combine(outDir, file), png);
                    manifest[pid] = file;
                }
                exported++;
            }
            catch (Exception ex) { errors++; Console.WriteLine($"[iconlist] err {path}: {ex.Message}"); }
        }
        Console.WriteLine($"[iconlist] textures: {exported}, errors: {errors}");
    }
}
