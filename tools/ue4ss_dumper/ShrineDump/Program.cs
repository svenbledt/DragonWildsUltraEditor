using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using CUE4Parse.Encryption.Aes;
using CUE4Parse.FileProvider;
using CUE4Parse.UE4.Versions;
using CUE4Parse.UE4.Objects.Core.Misc;
using CUE4Parse.MappingsProvider;
using CUE4Parse.MappingsProvider.Usmap;
using CUE4Parse.UE4.Assets.Exports;

// Static extraction of every BP_HealthShrine_C's UniqueShrineIdentifier FGuid
// from the cooked IoStore paks, formatted to the ShrinesUnlocked save string
// (%08X%08X%08X%08X of FGuid A/B/C/D). No in-game roaming needed.
class Program
{
    static int Main(string[] args)
    {
        string paks  = args.Length > 0 ? args[0] : @"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Content\Paks";
        string usmap = args.Length > 1 ? args[1] : @"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64\ue4ss\Mappings.usmap";
        string outFile = args.Length > 2 ? args[2] : "shrines_out.jsonl";
        string gameStr = args.Length > 3 ? args[3] : "GAME_UE5_4";

        EGame egame = Enum.Parse<EGame>(gameStr);
        Console.WriteLine($"[cfg] paks={paks}");
        Console.WriteLine($"[cfg] usmap={usmap}");
        Console.WriteLine($"[cfg] game={egame}");

        var provider = new DefaultFileProvider(paks, SearchOption.AllDirectories, new VersionContainer(egame));
        provider.Initialize();
        // Zero key: works for unencrypted index. If the game encrypts, Files stays 0.
        provider.SubmitKey(new FGuid(), new FAesKey("0x0000000000000000000000000000000000000000000000000000000000000000"));
        provider.MappingsContainer = new FileUsmapTypeMappingsProvider(usmap);

        Console.WriteLine($"[mount] files mounted: {provider.Files.Count}");
        if (provider.Files.Count == 0)
        {
            Console.WriteLine("[!] 0 files mounted - wrong UE version or the paks are AES-encrypted.");
            return 2;
        }

        if (gameStr.EndsWith("DISCOVER") || (args.Length > 4 && args[4] == "DISCOVER"))
        {
            var allUmap = provider.Files.Keys.Where(k => k.EndsWith(".umap", StringComparison.OrdinalIgnoreCase)).ToList();
            Console.WriteLine($"[umap] total .umap packages: {allUmap.Count}");
            var worldCells = allUmap.Where(k => k.Contains("maps/world", StringComparison.OrdinalIgnoreCase)).ToList();
            Console.WriteLine($"[umap] under maps/world: {worldCells.Count}");
            foreach (var s in worldCells.Take(12)) Console.WriteLine($"       {s}");

            // force-load the first several world cells to see WHY most return false
            int shown = 0;
            foreach (var cell in worldCells)
            {
                if (shown >= 6) break;
                shown++;
                try
                {
                    var pkg = provider.LoadPackage(cell);
                    var exps = pkg.GetExports().ToList();
                    Console.WriteLine($"[cell] OK {cell}  exports={exps.Count}: {string.Join(", ", exps.Take(12).Select(e => e.ExportType))}");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[cell] EX {cell}: {ex.GetType().Name}: {ex.Message}");
                }
            }

            // also try loading the blueprint itself as a sanity check
            var bp = provider.Files.Keys.FirstOrDefault(k => k.EndsWith("misc/bp_healthshrine.uasset", StringComparison.OrdinalIgnoreCase));
            Console.WriteLine($"[bp] blueprint pkg: {bp}");
            return 0;
        }

        // Candidate level/actor packages. Shrines are placed World-Partition actors,
        // which cook into packages under .../Maps/... - scan those.
        // Completeness: scan EVERY .umap in the pak (placed actors live in level
        // packages; the cook has no __ExternalActors__), regardless of /maps/.
        var mapPkgs = provider.Files.Keys
            .Where(k => k.EndsWith(".umap", StringComparison.OrdinalIgnoreCase))
            .ToList();
        Console.WriteLine($"[scan] candidate .umap packages: {mapPkgs.Count}");

        var guids = new SortedSet<string>(StringComparer.Ordinal);
        var classTally = new Dictionary<string, int>(StringComparer.Ordinal);
        int scanned = 0, errors = 0, hits = 0;

        foreach (var path in mapPkgs)
        {
            scanned++;
            if (scanned % 500 == 0)
                Console.WriteLine($"[scan] {scanned}/{mapPkgs.Count}  shrines so far: {guids.Count}");
            try
            {
                if (!provider.TryLoadPackage(path, out var pkg)) continue;
                foreach (var exp in pkg.GetExports())
                {
                    var cls = exp.ExportType ?? "";
                    if (cls.Contains("Shrine", StringComparison.OrdinalIgnoreCase)
                     || cls.Contains("Health", StringComparison.OrdinalIgnoreCase))
                        classTally[cls] = classTally.TryGetValue(cls, out var c) ? c + 1 : 1;

                    if (cls == "BP_HealthShrine_C")
                    {
                        if (exp.TryGetValue(out FGuid g, "UniqueShrineIdentifier"))
                        {
                            string hex = $"{g.A:X8}{g.B:X8}{g.C:X8}{g.D:X8}";
                            if (hex != "00000000000000000000000000000000")
                            {
                                if (guids.Add(hex)) hits++;
                            }
                        }
                    }
                }
            }
            catch (Exception)
            {
                errors++;
            }
        }

        Console.WriteLine();
        Console.WriteLine($"[done] scanned={scanned} errors={errors} unique shrine GUIDs={guids.Count}");
        Console.WriteLine("[classes seen containing Shrine/Health]:");
        foreach (var kv in classTally.OrderByDescending(x => x.Value))
            Console.WriteLine($"    {kv.Key} x{kv.Value}");

        using (var w = new StreamWriter(outFile, false))
        {
            foreach (var hex in guids)
                w.WriteLine($"{{\"PersistenceID\":\"{hex}\",\"__class\":\"BP_HealthShrine_C\"}}");
        }
        Console.WriteLine($"[out] wrote {guids.Count} ids -> {Path.GetFullPath(outFile)}");
        return 0;
    }
}
