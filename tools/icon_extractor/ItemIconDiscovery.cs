using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using CUE4Parse.FileProvider;
using CUE4Parse.UE4.Assets.Exports;
using CUE4Parse.UE4.Objects.UObject;

// Static icon discovery: reads each item's own cooked DataAsset directly from
// the paks (no in-game roaming, no runtime "was it loaded yet" luck) and
// exports the exact icon texture it references.
//
// How it works (verified 2026-07-06 against RSDragonwilds / GAME_UE5_6):
//   * Item DataAssets are cooked as plain .uasset packages, one item per file,
//     living under several content roots ("/Game/...", "/UmbralSands/...",
//     "/Fishing/...", one per installed content plugin/DLC). Their in-pak path
//     is always "<Root>/Content/<same-relative-path-as-the-/Root/-alias>.uasset"
//     regardless of which root it is - so a root-agnostic reverse lookup
//     (relative path after "/content/", case-insensitive) resolves all of them.
//   * The exact per-item relative path comes from tools/ue4ss_dumper's
//     ItemDumper_items.jsonl (`__fullname`, e.g. "ItemData /Game/Foo/Bar.Bar"),
//     already produced by an earlier in-game F8 dump for every item in
//     data/item_ids.py - it just wasn't previously used for icon lookup.
//   * PersistenceID is a plain StrProperty on the export, ALREADY the exact
//     url-safe-base64 string used everywhere else in this app (verified via
//     Abraxus Ring: TuG7zUS90qgd7BOHhOxd8Q round-trips byte for byte). No FGuid
//     decode/encoding step is involved anywhere in this pipeline.
//   * The icon is a SoftObjectProperty named "Icon" (verified across
//     TrinketItemData, HeldEquipmentData, WearableEquipmentData,
//     FishingRodHeldEquipmentData, and Blueprint-CDO item classes like
//     BP_Consumables_Food_C/BP_Consumables_Potion_C) whose FSoftObjectPath
//     AssetPathName is the texture's package path - present and resolvable even
//     though nothing is "loaded" at cook time, which is exactly why this works
//     for the 593 items the in-game dump recorded IconFile='' for.
static class ItemIconDiscovery
{
    public class Result
    {
        public Dictionary<string, string> PidToFile = new Dictionary<string, string>();
        public int ItemRecords, Resolved, PersistenceMismatch, NoIconProperty, TextureLoadFailed, PackageLoadFailed;
    }

    // Build a reverse lookup: lowercased "<path-after-.../Content/>" without
    // extension -> the actual provider.Files key. Root-agnostic, so it resolves
    // "/Game/...", "/UmbralSands/...", "/Fishing/..." etc. uniformly.
    public static Dictionary<string, string> BuildContentPathIndex(DefaultFileProvider provider)
    {
        var dict = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var key in provider.Files.Keys)
        {
            if (!key.EndsWith(".uasset", StringComparison.OrdinalIgnoreCase)) continue;
            var lower = key.Replace('\\', '/').ToLowerInvariant();
            var idx = lower.LastIndexOf("/content/", StringComparison.Ordinal);
            if (idx < 0) continue;
            var rel = lower.Substring(idx + "/content/".Length);
            rel = rel.Substring(0, rel.Length - ".uasset".Length);
            dict[rel] = key;   // last one wins on collision; collisions are rare and harmless here
        }
        return dict;
    }

    // Accepts either a UE4SS __fullname ("ClassName /Root/Path/Asset.Asset") or a
    // bare package path ("/Root/Path/Asset" from an FSoftObjectPath.AssetPathName).
    // Strips the leaf root segment (Game/UmbralSands/Fishing/...) and matches the
    // remainder, root-agnostically, against the content index.
    public static string ResolvePackagePath(Dictionary<string, string> contentIndex, string fullnameOrPath)
    {
        if (string.IsNullOrEmpty(fullnameOrPath)) return null;
        var sp = fullnameOrPath.IndexOf(' ');
        var pathPart = sp >= 0 ? fullnameOrPath.Substring(sp + 1) : fullnameOrPath;
        var dot = pathPart.LastIndexOf('.');
        var pkgPath = dot >= 0 ? pathPart.Substring(0, dot) : pathPart;
        pkgPath = pkgPath.TrimStart('/');
        var slash = pkgPath.IndexOf('/');
        if (slash < 0) return null;
        var rel = pkgPath.Substring(slash + 1).ToLowerInvariant();
        return contentIndex.TryGetValue(rel, out var full) ? full : null;
    }

    // itemsJsonlPath: tools/ue4ss_dumper/ItemDumper_items.jsonl - one JSON object
    // per line with at least "PersistenceID" and "__fullname".
    public static Result Discover(DefaultFileProvider provider, string itemsJsonlPath, string outDir)
    {
        var result = new Result();
        if (!File.Exists(itemsJsonlPath))
        {
            Console.WriteLine($"[static] items jsonl not found, skipping static discovery: {itemsJsonlPath}");
            return result;
        }

        var contentIndex = BuildContentPathIndex(provider);
        Console.WriteLine($"[static] content-path index: {contentIndex.Count} entries");

        var textureCache = new Dictionary<string, byte[]>(StringComparer.Ordinal);

        foreach (var line in File.ReadLines(itemsJsonlPath))
        {
            var trimmed = line.Trim();
            if (trimmed.Length == 0) continue;
            string pid, fullname;
            try
            {
                using var doc = JsonDocument.Parse(trimmed);
                var root = doc.RootElement;
                pid = root.TryGetProperty("PersistenceID", out var pidEl) ? pidEl.GetString() : null;
                fullname = root.TryGetProperty("__fullname", out var fnEl) ? fnEl.GetString() : null;
            }
            catch (JsonException)
            {
                continue;
            }
            if (string.IsNullOrEmpty(pid) || string.IsNullOrEmpty(fullname)) continue;
            result.ItemRecords++;

            var itemPkgKey = ResolvePackagePath(contentIndex, fullname);
            if (itemPkgKey == null) { result.PackageLoadFailed++; continue; }

            try
            {
                var pkg = provider.LoadPackage(itemPkgKey);
                var exports = pkg.GetExports().ToList();
                bool matched = false;

                // Primary: the export whose own PersistenceID StrProperty equals
                // the expected PID (the common case - one item per package).
                foreach (var exp in exports)
                {
                    var expPid = exp.GetOrDefault<string>("PersistenceID", null);
                    if (expPid != pid) continue;
                    matched = true;
                    TryExportIcon(provider, contentIndex, textureCache, exp, pid, outDir, result);
                    break;
                }

                // Fallback: some item classes (observed on BP_Consumables_RecipeUnlocker2_C
                // pattern-unlockers and BP_Consumables_SkillTome_C tomes, e.g. "Bramblemead
                // Cape" / "Tome of the Titan") never serialize a PersistenceID tag on the
                // export at all - it's produced at runtime some other way, not stored in the
                // cooked asset. When the package holds exactly one export carrying an Icon
                // soft reference, that's unambiguously *this* item's data (one item per
                // .uasset file, verified across the whole catalog), so use it directly.
                if (!matched)
                {
                    var iconCandidates = exports.Where(e => e.TryGetValue(out FSoftObjectPath _, "Icon", "IconFile", "IconTexture")).ToList();
                    if (iconCandidates.Count == 1)
                    {
                        matched = true;
                        TryExportIcon(provider, contentIndex, textureCache, iconCandidates[0], pid, outDir, result);
                    }
                }

                if (!matched) result.PersistenceMismatch++;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[static] package load error {itemPkgKey}: {ex.Message}");
                result.PackageLoadFailed++;
            }
        }

        return FinishAndReport(result);
    }

    // Reads the Icon soft reference off `exp`, resolves + decodes + resizes the
    // referenced texture (cached), writes "<pid>.png", and records it in `result`.
    static void TryExportIcon(DefaultFileProvider provider, Dictionary<string, string> contentIndex,
        Dictionary<string, byte[]> textureCache, UObject exp, string pid, string outDir, Result result)
    {
        if (!exp.TryGetValue(out FSoftObjectPath iconPath, "Icon", "IconFile", "IconTexture"))
        {
            result.NoIconProperty++;
            return;
        }
        var iconAssetPath = iconPath.AssetPathName.Text;
        if (string.IsNullOrEmpty(iconAssetPath)) { result.NoIconProperty++; return; }

        var texPkgKey = ResolvePackagePath(contentIndex, iconAssetPath);
        if (texPkgKey == null) { result.TextureLoadFailed++; return; }

        if (!textureCache.TryGetValue(texPkgKey, out var png))
        {
            try { png = TextureUtil.DecodePackageToPng64(provider, texPkgKey); }
            catch (Exception ex) { Console.WriteLine($"[static] texture decode error {texPkgKey}: {ex.Message}"); png = null; }
            textureCache[texPkgKey] = png;
        }
        if (png == null) { result.TextureLoadFailed++; return; }

        var file = pid + ".png";
        File.WriteAllBytes(Path.Combine(outDir, file), png);
        result.PidToFile[pid] = file;
        result.Resolved++;
    }

    static Result FinishAndReport(Result result)
    {
        Console.WriteLine($"[static] item records: {result.ItemRecords}");
        Console.WriteLine($"[static] resolved icons: {result.Resolved}");
        Console.WriteLine($"[static] persistence-id mismatch/not-found-in-package: {result.PersistenceMismatch}");
        Console.WriteLine($"[static] no icon property / empty soft path: {result.NoIconProperty}");
        Console.WriteLine($"[static] item package not found in pak index: {result.PackageLoadFailed}");
        Console.WriteLine($"[static] texture package not found/decoded: {result.TextureLoadFailed}");
        return result;
    }
}
