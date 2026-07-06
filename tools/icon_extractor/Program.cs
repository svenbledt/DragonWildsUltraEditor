using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CUE4Parse.Encryption.Aes;
using CUE4Parse.FileProvider;
using CUE4Parse.MappingsProvider;
using CUE4Parse.MappingsProvider.Usmap;
using CUE4Parse.UE4.Assets.Exports.Texture;
using CUE4Parse.UE4.Objects.Core.Misc;
using CUE4Parse.UE4.Versions;
using CUE4Parse_Conversion.Textures;
using SkiaSharp;

// Exports 64x64 PNG icons for catalog items straight from the cooked IoStore
// paks, keyed by PersistenceID. Dev-time only tool (not shipped); the app
// works fine with zero icons present (text-tile fallback in ui/icons.py).
class Program
{
    static int Main(string[] args)
    {
        // args: [paksDir] [usmapPath] [iconlistPath] [outDir] [onlyStem]
        string paks   = args.Length > 0 && !string.IsNullOrEmpty(args[0]) ? args[0] : @"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Content\Paks";
        string usmap  = args.Length > 1 && !string.IsNullOrEmpty(args[1]) ? args[1] : @"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64\ue4ss\Mappings.usmap";
        string list   = args.Length > 2 && !string.IsNullOrEmpty(args[2]) ? args[2] : Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "iconlist.txt");
        string outDir = args.Length > 3 && !string.IsNullOrEmpty(args[3]) ? args[3] : Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "..", "data", "icons");
        string only   = args.Length > 4 && !string.IsNullOrEmpty(args[4]) ? args[4].ToLowerInvariant() : null;

        Console.WriteLine($"[cfg] paks={paks}");
        Console.WriteLine($"[cfg] usmap={usmap}");
        Console.WriteLine($"[cfg] iconlist={list}");
        Console.WriteLine($"[cfg] outDir={outDir}");

        // stem ("t_icon_runic_ring") -> list of PersistenceIDs sharing it
        var wanted = new Dictionary<string, List<string>>();
        foreach (var line in File.ReadAllLines(list))
        {
            var parts = line.Split('\t');
            if (parts.Length != 2) continue;
            var stem = Path.GetFileNameWithoutExtension(parts[1]).ToLowerInvariant();
            if (only != null && stem != only) continue;
            if (!wanted.TryGetValue(stem, out var pids))
                wanted[stem] = pids = new List<string>();
            pids.Add(parts[0]);
        }
        Console.WriteLine($"[cfg] {wanted.Count} unique icon textures wanted");

        // ---- provider setup: copied verbatim from ShrineDump/Program.cs, ----
        // ---- except EGame is pinned to GAME_UE5_6 (the version proven to ----
        // ---- correctly parse this game's cooked packages).               ----
        EGame egame = EGame.GAME_UE5_6;
        Console.WriteLine($"[cfg] game={egame}");

        var provider = new DefaultFileProvider(paks, SearchOption.AllDirectories, new VersionContainer(egame));
        provider.Initialize();
        // Zero key: works for unencrypted index. If the game encrypts, Files stays 0.
        provider.SubmitKey(new FGuid(), new FAesKey("0x0000000000000000000000000000000000000000000000000000000000000000"));
        provider.MappingsContainer = new FileUsmapTypeMappingsProvider(usmap);

        Console.WriteLine($"[mount] files: {provider.Files.Count}");
        if (provider.Files.Count == 0) { Console.WriteLine("[!] nothing mounted"); return 2; }

        Directory.CreateDirectory(outDir);
        var manifest = new SortedDictionary<string, string>();
        int exported = 0, errors = 0;
        foreach (var path in provider.Files.Keys.ToList())
        {
            if (!path.EndsWith(".uasset", StringComparison.OrdinalIgnoreCase)) continue;
            var stem = Path.GetFileNameWithoutExtension(path).ToLowerInvariant();
            if (!wanted.TryGetValue(stem, out var pids)) continue;
            try
            {
                var pkg = provider.LoadPackage(path);
                var tex = pkg.GetExports().OfType<UTexture2D>().FirstOrDefault();
                if (tex == null) continue;
                var ctex = tex.Decode(ETexturePlatform.DesktopMobile);   // CUE4Parse_Conversion.Textures
                if (ctex == null) continue;
                using var bmp = ctex.ToSkBitmap();
                if (bmp == null) continue;
                using var resized = bmp.Resize(new SKImageInfo(64, 64), SKFilterQuality.High) ?? bmp;
                using var img = SKImage.FromBitmap(resized);
                using var png = img.Encode(SKEncodedImageFormat.Png, 100);
                foreach (var pid in pids)
                {
                    var file = pid + ".png";   // PIDs are url-safe base64: filename-safe
                    using var fs = File.Create(Path.Combine(outDir, file));
                    png.SaveTo(fs);
                    manifest[pid] = file;
                }
                exported++;
            }
            catch (Exception ex) { errors++; Console.WriteLine($"[err] {path}: {ex.Message}"); }
        }
        File.WriteAllText(Path.Combine(outDir, "manifest.json"),
            JsonSerializer.Serialize(manifest, new JsonSerializerOptions { WriteIndented = true }));
        Console.WriteLine($"[done] textures: {exported}, errors: {errors}, pids mapped: {manifest.Count}");
        return 0;
    }
}
