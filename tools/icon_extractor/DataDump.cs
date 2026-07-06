using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using CUE4Parse.Encryption.Aes;
using CUE4Parse.FileProvider;
using CUE4Parse.MappingsProvider.Usmap;
using CUE4Parse.UE4.Assets.Exports;
using CUE4Parse.UE4.Objects.Core.i18N;
using CUE4Parse.UE4.Objects.Core.Misc;
using CUE4Parse.UE4.Objects.UObject;
using CUE4Parse.UE4.Versions;

// Static game-data extractor: dumps every item / recipe / building piece /
// mount DataAsset straight from the cooked paks — no UE4SS, no running game.
//
// Registry accuracy: each Dominion subsystem registers only assets found
// under its config-declared DataPaths (RSDragonwilds/Config/DefaultGame.ini,
// e.g. [/Script/Dominion.RecipeSubsystem] +DataPaths="/Game/Gameplay/Items").
// Ids OUTSIDE those paths are never registered, and one unregistered id in a
// save list aborts the strict-mode character load. Every dumped record
// carries "__registered" so the build_*.py generators can keep exactly the
// game-accepted set and the Save doctor can blocklist the rest.
//
// Output: <outDir>/ItemDumper_{items,recipes,buildings,mounts}.jsonl in the
// same record shape as the retired UE4SS ItemDumper (PersistenceID,
// __fullname, __class, SourceString, Weight, MaxStackSize, ...), plus
// ItemDumper_diagnostics.txt. SourceString here is the cooked FText source —
// always English, unlike the runtime dump which localized names.
static class DataDump
{
    const string PAKS = @"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Content\Paks";
    const string USMAP = @"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64\ue4ss\Mappings.usmap";

    static readonly string[] RootClasses = { "ItemData", "RecipeData", "BuildingPieceData", "MountDataAsset" };

    public static int Run(string[] args)
    {
        // --dump-data probe <substr>: verbose classification of matching
        // packages only; writes go to a temp dir so the real dumps stay intact
        string probeArg = args.Length > 2 && args[1] == "probe" ? args[2].ToLowerInvariant() : null;
        string outDir = probeArg != null
            ? Path.Combine(Path.GetTempPath(), "DataDumpProbe")
            : args.Length > 1 && !string.IsNullOrEmpty(args[1])
                ? args[1]
                : Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "game_dump"));
        Directory.CreateDirectory(outDir);
        Console.WriteLine($"[dump] outDir={outDir}");

        var provider = new DefaultFileProvider(PAKS, SearchOption.AllDirectories, new VersionContainer(EGame.GAME_UE5_6));
        provider.Initialize();
        provider.SubmitKey(new FGuid(), new FAesKey("0x0000000000000000000000000000000000000000000000000000000000000000"));
        provider.MappingsContainer = new FileUsmapTypeMappingsProvider(USMAP);
        Console.WriteLine($"[mount] files: {provider.Files.Count}");
        if (provider.Files.Count == 0) return 2;
        _provider = provider;
        _contentIndex = ItemIconDiscovery.BuildContentPathIndex(provider);
        LoadLocres();

        // ---- registry DataPaths from the game's own config ----
        var ini = Encoding.UTF8.GetString(provider.SaveAsset("RSDragonwilds/Config/DefaultGame.ini"));
        var dataPaths = new Dictionary<string, List<string>>
        {
            ["items"] = SectionDataPaths(ini, "/Script/Dominion.ItemSubsystem"),
            ["recipes"] = SectionDataPaths(ini, "/Script/Dominion.RecipeSubsystem"),
            ["buildings"] = SectionDataPaths(ini, "/Script/Dominion.BuildingPieceSubsystem"),
            ["mounts"] = MountScanDirs(ini),
        };
        var diag = new StringBuilder();
        foreach (var kv in dataPaths)
        {
            Console.WriteLine($"[cfg] {kv.Key}: {kv.Value.Count} DataPaths");
            diag.AppendLine($"{kv.Key} DataPaths:");
            foreach (var p in kv.Value) diag.AppendLine($"  {p}");
            if (kv.Value.Count == 0) { Console.WriteLine($"[!] no DataPaths parsed for {kv.Key}"); return 3; }
        }

        // ---- native subclass closure from the usmap ----
        var usmap = new FileUsmapTypeMappingsProvider(USMAP);
        usmap.Reload();
        var types = usmap.MappingsForGame.Types;
        var rootOf = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var name in types.Keys)
        {
            var cur = name;
            var guard = 0;
            while (cur != null && guard++ < 64)
            {
                if (RootClasses.Contains(cur)) { rootOf[name] = cur; break; }
                cur = types.TryGetValue(cur, out var s) ? s.SuperType : null;
            }
        }
        Console.WriteLine($"[usmap] native subclasses matched: {rootOf.Count}");

        // ---- scan candidate packages ----
        var writers = new Dictionary<string, StreamWriter>
        {
            ["ItemData"] = new StreamWriter(Path.Combine(outDir, "ItemDumper_items.jsonl"), false, new UTF8Encoding(false)),
            ["RecipeData"] = new StreamWriter(Path.Combine(outDir, "ItemDumper_recipes.jsonl"), false, new UTF8Encoding(false)),
            ["BuildingPieceData"] = new StreamWriter(Path.Combine(outDir, "ItemDumper_buildings.jsonl"), false, new UTF8Encoding(false)),
            ["MountDataAsset"] = new StreamWriter(Path.Combine(outDir, "ItemDumper_mounts.jsonl"), false, new UTF8Encoding(false)),
        };
        var catOfRoot = new Dictionary<string, string>
        {
            ["ItemData"] = "items", ["RecipeData"] = "recipes",
            ["BuildingPieceData"] = "buildings", ["MountDataAsset"] = "mounts",
        };
        var counts = new Dictionary<string, int[]>();  // root -> [registered, unregistered]
        foreach (var r in RootClasses) counts[r] = new int[2];
        var bpCache = new Dictionary<string, string>();  // blueprint class name -> root or ""
        int scanned = 0, errors = 0;

        string probe = probeArg;

        foreach (var key in provider.Files.Keys)
        {
            if (!key.EndsWith(".uasset", StringComparison.OrdinalIgnoreCase)) continue;
            if (probe != null)
            {
                if (!key.ToLowerInvariant().Contains(probe)) continue;
                foreach (var e in provider.LoadPackage(key).GetExports())
                {
                    Console.WriteLine($"[probe] {key} export={e.Name} class={e.ExportType} " +
                        $"root={RootFor(e, rootOf, bpCache) ?? "-"} pid={e.GetOrDefault<string>("PersistenceID") ?? "-"}");
                    Console.WriteLine(Newtonsoft.Json.JsonConvert.SerializeObject(e, Newtonsoft.Json.Formatting.Indented));
                }
                continue;
            }
            var lower = key.ToLowerInvariant();
            if (!lower.Contains("/content/gameplay/") && !lower.Contains("/content/chinchompa")) continue;
            var gamePath = GamePath(key);
            if (gamePath == null) continue;

            IEnumerable<UObject> exports;
            try { exports = provider.LoadPackage(key).GetExports(); }
            catch (Exception ex)
            {
                errors++;
                Console.WriteLine($"[err] {key}: {ex.Message.Split('\n')[0]}");
                continue;
            }
            scanned++;
            if (scanned % 2000 == 0) Console.WriteLine($"[scan] {scanned} packages...");

            foreach (var exp in exports)
            {
                // class-default objects (templates inside BP packages) are
                // not real game assets — the subsystems never register them
                if (exp.Name.StartsWith("Default__")) continue;
                var root = RootFor(exp, rootOf, bpCache);
                if (root == null) continue;
                var pid = ResolvePid(exp);
                // mounts are referenced by asset name (MountDataAsset:DA_x),
                // not by PersistenceID — everything else needs a pid
                if (string.IsNullOrEmpty(pid) && root != "MountDataAsset") continue;

                bool registered = dataPaths[catOfRoot[root]].Any(dp =>
                    gamePath.StartsWith(dp + "/", StringComparison.OrdinalIgnoreCase) ||
                    gamePath.Equals(dp, StringComparison.OrdinalIgnoreCase));
                counts[root][registered ? 0 : 1]++;

                var rec = new Dictionary<string, object>
                {
                    ["__fullname"] = $"{exp.ExportType} {gamePath}.{exp.Name}",
                    ["__class"] = exp.ExportType,
                    ["__registered"] = registered,
                };
                if (!string.IsNullOrEmpty(pid)) rec["PersistenceID"] = pid;
                var disp = Txt(exp, "Name") ?? Txt(exp, "DisplayName") ?? Txt(exp, "ItemName") ?? Txt(exp, "Title");
                if (disp != null) { rec["SourceString"] = disp; rec["Name"] = disp; }
                foreach (var f in new[] { "Weight" })
                { var v = exp.GetOrDefault<float?>(f); if (v.HasValue) rec[f] = v.Value; }
                foreach (var f in new[] { "Durability", "PowerLevel", "MaxStackSize", "VitalShield" })
                { var v = exp.GetOrDefault<int?>(f); if (v.HasValue) rec[f] = v.Value; }
                var cat = exp.GetOrDefault<FName>("Category");
                if (!cat.IsNone) rec["Category"] = cat.Text;
                writers[root].WriteLine(JsonSerializer.Serialize(rec));
            }
        }
        foreach (var w in writers.Values) w.Dispose();

        diag.AppendLine($"packages scanned: {scanned}, load errors: {errors}");
        foreach (var r in RootClasses)
        {
            var line = $"{catOfRoot[r]}: {counts[r][0]} registered + {counts[r][1]} unregistered (junk)";
            Console.WriteLine("[done] " + line);
            diag.AppendLine(line);
        }
        File.WriteAllText(Path.Combine(outDir, "ItemDumper_diagnostics.txt"), diag.ToString());
        return 0;
    }

    // "RSDragonwilds/Content/X.uasset" -> "/Game/X";
    // "RSDragonwilds/Plugins/**/Name/Content/X.uasset" -> "/Name/X"
    static string GamePath(string key)
    {
        var noExt = key.Substring(0, key.Length - ".uasset".Length);
        const string game = "RSDragonwilds/Content/";
        if (noExt.StartsWith(game, StringComparison.OrdinalIgnoreCase))
            return "/Game/" + noExt.Substring(game.Length);
        var m = Regex.Match(noExt, @"^RSDragonwilds/Plugins/(?:.+/)?([^/]+)/Content/(.+)$", RegexOptions.IgnoreCase);
        return m.Success ? $"/{m.Groups[1].Value}/{m.Groups[2].Value}" : null;
    }

    static string RootFor(UObject exp, Dictionary<string, string> rootOf, Dictionary<string, string> bpCache)
    {
        var cls = exp.ExportType;
        if (rootOf.TryGetValue(cls, out var native)) return native;
        if (!cls.EndsWith("_C")) return null;
        if (bpCache.TryGetValue(cls, out var cached)) return cached == "" ? null : cached;
        string found = "";
        try
        {
            var cur = exp.Class?.Load() as UStruct;
            var guard = 0;
            while (cur != null && guard++ < 64)
            {
                if (rootOf.TryGetValue(cur.Name, out var r) || RootClasses.Contains(cur.Name))
                { found = r ?? cur.Name; break; }
                cur = cur.SuperStruct?.Load<UStruct>();
            }
        }
        catch { }
        bpCache[cls] = found;
        return found == "" ? null : found;
    }

    // A data asset that doesn't override PersistenceID inherits its blueprint
    // CDO's default (e.g. DA_Consumable_Pattern_Armor_Cape_Bramblemead gets
    // BP_Consumables_RecipeUnlocker2_C's) — walk the template chain like the
    // engine does.
    static string ResolvePid(UObject exp)
    {
        var cur = exp;
        for (var i = 0; cur != null && i < 8; i++)
        {
            var pid = cur.GetOrDefault<string>("PersistenceID");
            if (!string.IsNullOrEmpty(pid)) return pid;
            try { cur = cur.Template?.Load() as UObject; }
            catch { return null; }
        }
        return null;
    }

    // set once in Run(); used by Txt to resolve string-table FTexts (skill
    // capes, mount consumables, quest items keep their names in ST_ItemNames
    // rather than inline SourceStrings)
    static DefaultFileProvider _provider;
    static Dictionary<string, string> _contentIndex;
    // key -> English string from Game.locres, the last-resort name source:
    // a few real items (the skill mastery capes) reference string-table keys
    // that no longer exist in ST_ItemNames but ARE still in the compiled
    // localization the running game shows.
    static Dictionary<string, string> _locres;

    static void LoadLocres()
    {
        _locres = new Dictionary<string, string>(StringComparer.Ordinal);
        try
        {
            var data = _provider.SaveAsset("RSDragonwilds/Content/Localization/Game/en/Game.locres");
            var res = new CUE4Parse.UE4.Localization.FTextLocalizationResource(
                new CUE4Parse.UE4.Readers.FByteArchive("Game.locres", data));
            foreach (var ns in res.Entries)
                foreach (var kv in ns.Value)
                    _locres[kv.Key.Str] = kv.Value.LocalizedString;
        }
        catch (Exception ex) { Console.WriteLine($"[locres] load failed: {ex.Message}"); }
        Console.WriteLine($"[locres] entries: {_locres.Count}");
    }

    static string Txt(UObject exp, string prop)
    {
        // like ResolvePid: an asset may inherit its display name from its
        // blueprint CDO's defaults, so walk the template chain
        var cur = exp;
        for (var i = 0; cur != null && i < 8; i++)
        {
            FText t = null;
            try
            {
                t = cur.GetOrDefault<FText>(prop);
                var s = t == null ? null : QuestDiscovery.TextOf(_provider, _contentIndex, t);
                if (!string.IsNullOrEmpty(s) && s != "None") return s;
            }
            catch { }
            // dangling string-table key: fall back to the compiled locres
            if (t?.TextHistory is CUE4Parse.UE4.Objects.Core.i18N.FTextHistory.StringTableEntry ste
                && !string.IsNullOrEmpty(ste.Key)
                && _locres.TryGetValue(ste.Key, out var loc)
                && !string.IsNullOrEmpty(loc))
                return loc;
            try { cur = cur.Template?.Load() as UObject; }
            catch { return null; }
        }
        return null;
    }

    static List<string> SectionDataPaths(string ini, string section)
    {
        var m = Regex.Match(ini, Regex.Escape("[" + section + "]") + @"(.*?)(?=\r?\n\[)", RegexOptions.Singleline);
        if (!m.Success) return new List<string>();
        return Regex.Matches(m.Groups[1].Value, @"\+DataPaths=""([^""\r\n]+)""?")
            .Select(x => x.Groups[1].Value.TrimEnd('/', '"')).Distinct().ToList();
    }

    static List<string> MountScanDirs(string ini)
    {
        var m = Regex.Match(ini, @"PrimaryAssetType=""MountDataAsset"".*?Directories=\((.*?)\)\)", RegexOptions.Singleline);
        if (!m.Success) return new List<string>();
        return Regex.Matches(m.Groups[1].Value, @"Path=""([^""]+)""")
            .Select(x => x.Groups[1].Value.TrimEnd('/')).Distinct().ToList();
    }
}
