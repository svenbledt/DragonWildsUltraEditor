using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using CUE4Parse.Encryption.Aes;
using CUE4Parse.FileProvider;
using CUE4Parse.MappingsProvider;
using CUE4Parse.MappingsProvider.Usmap;
using CUE4Parse.UE4.Assets.Exports;
using CUE4Parse.UE4.Objects.Core.Misc;
using CUE4Parse.UE4.Versions;
using Newtonsoft.Json;

// Quest definition dumper (--quests). See Program.cs for the icon modes.
// Exploration submodes:
//   --quests raw <AssetNameSubstring>   dump full property JSON of matching quest packages
//   --quests enums                      list usmap enums whose name contains "quest"
//   --quests                            full dump to quests_dump.json
static class QuestDiscovery
{
    static DefaultFileProvider MakeProvider()
    {
        var paks = @"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Content\Paks";
        var usmap = @"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64\ue4ss\Mappings.usmap";
        var provider = new DefaultFileProvider(paks, SearchOption.AllDirectories, new VersionContainer(EGame.GAME_UE5_6));
        provider.Initialize();
        provider.SubmitKey(new FGuid(), new FAesKey("0x0000000000000000000000000000000000000000000000000000000000000000"));
        provider.MappingsContainer = new FileUsmapTypeMappingsProvider(usmap);
        Console.WriteLine($"[quests] mounted files: {provider.Files.Count}");
        try
        {
            var n = provider.LoadLocalization(ELanguage.English);
            Console.WriteLine($"[quests] localization entries loaded: {n}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[quests] localization load failed: {ex.Message}");
        }
        return provider;
    }

    static List<string> FindQuestPackages(DefaultFileProvider provider)
    {
        return provider.Files.Keys
            .Where(k => k.EndsWith(".uasset", StringComparison.OrdinalIgnoreCase))
            .Where(k =>
            {
                var norm = k.Replace('\\', '/');
                if (norm.IndexOf("Gameplay/Quests/", StringComparison.OrdinalIgnoreCase) < 0) return false;
                var name = Path.GetFileNameWithoutExtension(norm);
                return name.StartsWith("Quest_", StringComparison.OrdinalIgnoreCase);
            })
            .OrderBy(k => k, StringComparer.OrdinalIgnoreCase)
            .ToList();
    }

    public static int Run(string[] args)
    {
        var sub = args.Length > 1 ? args[1].ToLowerInvariant() : "";

        if (sub == "enums")
        {
            var usmap = new FileUsmapTypeMappingsProvider(@"F:\SteamLibrary\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64\ue4ss\Mappings.usmap");
            usmap.Reload();
            var mappings = usmap.MappingsForGame;
            foreach (var kv in mappings.Enums.OrderBy(k => k.Key))
            {
                if (kv.Key.IndexOf("quest", StringComparison.OrdinalIgnoreCase) < 0) continue;
                Console.WriteLine($"enum {kv.Key}:");
                foreach (var e in kv.Value.OrderBy(e => e.Key))
                    Console.WriteLine($"  {e.Key} = {e.Value}");
            }
            return 0;
        }

        var provider = MakeProvider();
        var questPkgs = FindQuestPackages(provider);
        Console.WriteLine($"[quests] quest packages found: {questPkgs.Count}");

        if (sub == "raw")
        {
            var needle = args.Length > 2 ? args[2].ToLowerInvariant() : "";
            foreach (var pkgPath in questPkgs)
            {
                if (!Path.GetFileNameWithoutExtension(pkgPath).ToLowerInvariant().Contains(needle)) continue;
                Console.WriteLine($"==== {pkgPath} ====");
                try
                {
                    var pkg = provider.LoadPackage(pkgPath);
                    var exports = pkg.GetExports().ToList();
                    foreach (var exp in exports)
                    {
                        Console.WriteLine($"---- export: {exp.Name} ({exp.ExportType}) ----");
                        Console.WriteLine(JsonConvert.SerializeObject(exp, Formatting.Indented));
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[quests] load error: {ex}");
                }
            }
            return 0;
        }

        if (sub == "rawpkg")
        {
            // raw-dump an arbitrary package by path substring (QF_ blueprints etc.)
            var needle = args.Length > 2 ? args[2].ToLowerInvariant() : "";
            foreach (var key in provider.Files.Keys.OrderBy(k => k))
            {
                if (!key.EndsWith(".uasset", StringComparison.OrdinalIgnoreCase)) continue;
                if (!key.ToLowerInvariant().Contains(needle)) continue;
                Console.WriteLine($"==== {key} ====");
                try
                {
                    var pkg = provider.LoadPackage(key);
                    foreach (var exp in pkg.GetExports())
                    {
                        Console.WriteLine($"---- export: {exp.Name} ({exp.ExportType}) ----");
                        Console.WriteLine(JsonConvert.SerializeObject(exp, Formatting.Indented));
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[quests] load error: {ex}");
                }
            }
            return 0;
        }

        if (sub == "survey")
        {
            SurveyQuestFlows(provider);
            return 0;
        }

        if (sub == "graph")
        {
            var needle = args.Length > 2 ? args[2].ToLowerInvariant() : "";
            foreach (var pkgPath in FindQuestFlowPackages(provider))
            {
                if (!Path.GetFileNameWithoutExtension(pkgPath).ToLowerInvariant().Contains(needle)) continue;
                Console.WriteLine($"==== {pkgPath} ====");
                var pkg = provider.LoadPackage(pkgPath);
                foreach (var exp in pkg.GetExports())
                {
                    var guid = exp.GetOrDefault<FGuid>("Compiled_NodeGUID");
                    var outs = exp.GetOrDefault<FGuid[]>("OutputConnections") ?? Array.Empty<FGuid>();
                    var parent = exp.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex>("ParentNode");
                    string extra = "";
                    var q = exp.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex>("QuestData");
                    if (q != null && !q.IsNull) extra += $" quest={ObjName(q)}";
                    var item = exp.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex>("ItemData");
                    if (item != null && !item.IsNull) extra += $" item={ObjName(item)}";
                    Console.WriteLine($"{exp.Name} [{exp.ExportType}] guid={guid} parent={(parent != null && !parent.IsNull ? ObjName(parent) : "-")} outs=[{string.Join(",", outs.Select(g => g.ToString()))}]{extra}");
                }
            }
            return 0;
        }

        return FullDump(provider);
    }

    // ---------------------------------------------------------------- full dump

    class RewardEntry
    {
        public string item_id;
        public string asset;
        public int count = 1;
        public string type = "item";   // "item" | "mount_unlock"
    }

    class QuestEntry
    {
        public string quest_id;
        public string asset;
        public string path;
        public string name;
        public string description;
        public string category;
        public List<RewardEntry> rewards = new List<RewardEntry>();
        public List<string> objectives = new List<string>();
        public Dictionary<string, string> objective_texts = new Dictionary<string, string>();
        public string internal_name;
        public string region;
        public bool is_main_quest;
        public bool is_task_quest;
        public bool hidden_in_quest_list;
    }

    // FText resolution. CUE4Parse resolves string-table FTexts automatically for
    // /Game/ paths, but NOT for game-feature plugin mounts (/DowdunReach/,
    // /UmbralSands/, /Fishing/): their virtual roots aren't registered on this
    // provider, so we resolve those manually through the same root-agnostic
    // content index the icon pipeline uses.
    static Dictionary<string, Dictionary<string, string>> _stringTableCache =
        new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase);

    internal static string TextOf(DefaultFileProvider provider, Dictionary<string, string> contentIndex,
        CUE4Parse.UE4.Objects.Core.i18N.FText t)
    {
        if (t == null) return null;
        var s = t.Text;
        if (!string.IsNullOrEmpty(s) && s != "None") return s;

        if (t.TextHistory is CUE4Parse.UE4.Objects.Core.i18N.FTextHistory.StringTableEntry ste)
        {
            var tableId = ste.TableId.Text;    // "/Root/Path/ST_X.ST_X"
            var key = ste.Key;
            if (string.IsNullOrEmpty(tableId) || string.IsNullOrEmpty(key)) return null;
            if (!_stringTableCache.TryGetValue(tableId, out var table))
            {
                table = new Dictionary<string, string>(StringComparer.Ordinal);
                var pkgKey = ItemIconDiscovery.ResolvePackagePath(contentIndex, tableId);
                if (pkgKey != null)
                {
                    try
                    {
                        foreach (var exp in provider.LoadPackage(pkgKey).GetExports())
                        {
                            if (exp is CUE4Parse.UE4.Assets.Exports.Internationalization.UStringTable ust)
                                foreach (var kv in ust.StringTable.KeysToEntries)
                                    table[kv.Key] = kv.Value;
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"[quests] string table load failed {tableId}: {ex.Message}");
                    }
                }
                _stringTableCache[tableId] = table;
            }
            return table.TryGetValue(key, out var v) ? v : null;
        }
        return null;
    }

    static int FullDump(DefaultFileProvider provider)
    {
        var questPkgs = FindQuestPackages(provider);

        // Item asset-name -> persistence id, from the static game dump (covers
        // BP_Consumables_* classes whose cooked asset has no PersistenceID tag).
        var namePid = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        var itemsJsonl = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "game_dump", "ItemDumper_items.jsonl");
        if (File.Exists(itemsJsonl))
        {
            foreach (var line in File.ReadLines(itemsJsonl))
            {
                try
                {
                    using var doc = System.Text.Json.JsonDocument.Parse(line);
                    var root = doc.RootElement;
                    var pid = root.TryGetProperty("PersistenceID", out var p) ? p.GetString() : null;
                    var fn = root.TryGetProperty("__fullname", out var f) ? f.GetString() : null;
                    if (pid == null || fn == null) continue;
                    var dot = fn.LastIndexOf('.');
                    if (dot >= 0) namePid[fn.Substring(dot + 1)] = pid;
                }
                catch { }
            }
        }
        Console.WriteLine($"[quests] item name->pid map: {namePid.Count} entries");

        var contentIndex = ItemIconDiscovery.BuildContentPathIndex(provider);

        // 1) base quest records
        var byExportName = new Dictionary<string, QuestEntry>(StringComparer.OrdinalIgnoreCase);
        var entries = new List<QuestEntry>();
        foreach (var pkgPath in questPkgs)
        {
            try
            {
                var pkg = provider.LoadPackage(pkgPath);
                foreach (var exp in pkg.GetExports())
                {
                    if (exp.ExportType != "QuestData") continue;
                    var e = new QuestEntry
                    {
                        quest_id = exp.GetOrDefault<string>("PersistenceID"),
                        asset = exp.Name,
                        path = pkgPath.Replace('\\', '/'),
                        name = TextOf(provider, contentIndex, exp.GetOrDefault<CUE4Parse.UE4.Objects.Core.i18N.FText>("QuestName")),
                        description = TextOf(provider, contentIndex, exp.GetOrDefault<CUE4Parse.UE4.Objects.Core.i18N.FText>("QuestDescription")),
                        internal_name = exp.GetOrDefault<string>("InternalName"),
                    };
                    var region = exp.GetOrDefault<CUE4Parse.UE4.Assets.Objects.FPropertyTag>("QuestRegion");
                    e.region = region?.Tag?.GenericValue?.ToString()?.Replace("EQuestRegion::", "");

                    // classification: FTUE naming wins (most FTUE quests also
                    // carry bIsMainQuest=true because they lead into the main
                    // line, but the editor wants them shown as tutorial), then
                    // the explicit bIsMainQuest bool, otherwise side. The raw
                    // bool is preserved in is_main_quest.
                    bool isMain = exp.GetOrDefault<bool>("bIsMainQuest", false);
                    bool isFtue = e.asset.IndexOf("FTUE", StringComparison.OrdinalIgnoreCase) >= 0
                               || pkgPath.IndexOf("FTUE", StringComparison.OrdinalIgnoreCase) >= 0;
                    e.is_main_quest = isMain;
                    e.is_task_quest = exp.GetOrDefault<bool>("bIsTaskQuest", false);
                    e.hidden_in_quest_list = exp.GetOrDefault<bool>("bHideInQuestList", false);
                    e.category = isFtue ? "tutorial" : (isMain ? "main" : "side");

                    var objMap = exp.GetOrDefault<CUE4Parse.UE4.Assets.Objects.UScriptMap>("ObjectiveTexts");
                    if (objMap != null)
                    {
                        foreach (var kv in objMap.Properties)
                        {
                            var id = kv.Key?.GenericValue?.ToString();
                            if (id == null) continue;
                            e.objectives.Add(id);
                            string txt = null;
                            if (kv.Value?.GenericValue is CUE4Parse.UE4.Objects.Core.i18N.FText ft) txt = TextOf(provider, contentIndex, ft);
                            e.objective_texts[id] = txt;
                        }
                    }

                    entries.Add(e);
                    byExportName[exp.Name] = e;
                    break;   // one QuestData per package
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[quests] quest load error {pkgPath}: {ex.Message}");
            }
        }
        Console.WriteLine($"[quests] quest records: {entries.Count}");

        // 2) rewards from QF_* conversation flows.
        // A quest's rewards are the Give-item nodes on the same task chain as its
        // QFT_CompleteQuest node: walk backward along the (unique) ParentNode
        // chain and forward along OutputConnections, bounded, collecting
        // QFT_GiveItemToPlayer / QFT_GiveItemsToPlayer / QFT_UnlockMount nodes.
        var itemPidCache = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        int flowsScanned = 0;
        foreach (var pkgPath in FindQuestFlowPackages(provider))
        {
            List<UObject> exports;
            try { exports = provider.LoadPackage(pkgPath).GetExports().ToList(); }
            catch (Exception ex) { Console.WriteLine($"[quests] flow load error {pkgPath}: {ex.Message}"); continue; }
            flowsScanned++;

            var byGuid = new Dictionary<FGuid, UObject>();
            var byName = new Dictionary<string, UObject>(StringComparer.Ordinal);
            foreach (var exp in exports)
            {
                byName[exp.Name] = exp;
                var g = exp.GetOrDefault<FGuid>("Compiled_NodeGUID");
                if (g != default) byGuid[g] = exp;
            }

            foreach (var exp in exports)
            {
                var t = exp.ExportType;
                var questRefs = new List<string>();
                if (t == "QFT_CompleteQuest_C" || t == "QFT_CompleteQuest_RestlessGhost_C")
                {
                    var q = exp.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex>("QuestData");
                    var n = ObjName(q);
                    if (n != null) questRefs.Add(n);
                }
                else if (t == "QFT_CompleteQuests_C")
                {
                    var arr = exp.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex[]>("QuestData");
                    if (arr != null) foreach (var q in arr) { var n = ObjName(q); if (n != null) questRefs.Add(n); }
                }
                if (questRefs.Count == 0) continue;

                var giveNodes = CollectChainGiveNodes(exp, byGuid, byName);
                foreach (var qname in questRefs)
                {
                    if (!byExportName.TryGetValue(qname, out var quest)) continue;
                    foreach (var give in giveNodes)
                        AddRewards(provider, contentIndex, namePid, itemPidCache, give, quest);
                }
            }
        }
        Console.WriteLine($"[quests] quest-flow packages scanned: {flowsScanned}");

        // 3) write output
        var outPath = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "quests_dump.json");
        outPath = Path.GetFullPath(outPath);
        var json = JsonConvert.SerializeObject(entries.OrderBy(e => e.asset, StringComparer.OrdinalIgnoreCase), Formatting.Indented);
        File.WriteAllText(outPath, json);
        Console.WriteLine($"[quests] wrote {entries.Count} quests -> {outPath}");
        Console.WriteLine($"[quests] with rewards: {entries.Count(e => e.rewards.Count > 0)}");
        foreach (var g in entries.GroupBy(e => e.category))
            Console.WriteLine($"[quests] category {g.Key}: {g.Count()}");
        return 0;
    }

    // Walk the task chain around a CompleteQuest node. Backward: unique
    // ParentNode chain (stops at conversation entry / after passing a dialogue
    // prompt boundary of 2 prompts, or 20 hops). Forward: OutputConnections BFS
    // (bounded 8 hops). Collect give/unlock nodes seen on the way.
    static List<UObject> CollectChainGiveNodes(UObject completeNode,
        Dictionary<FGuid, UObject> byGuid, Dictionary<string, UObject> byName)
    {
        var found = new List<UObject>();
        var seen = new HashSet<string>(StringComparer.Ordinal);

        bool IsGive(UObject n) =>
            n.ExportType == "QFT_GiveItemToPlayer_C" ||
            n.ExportType == "QFT_GiveItemsToPlayer_C" ||
            n.ExportType == "QFT_UnlockMount_C" ||
            n.ExportType == "QFT_GiveCraftingRecipe_C";

        // backward: single parent chain
        var cur = completeNode;
        int hops = 0, promptsCrossed = 0;
        while (cur != null && hops++ < 20)
        {
            var parentIdx = cur.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex>("ParentNode");
            var pname = parentIdx != null && !parentIdx.IsNull ? ObjName(parentIdx) : null;
            if (pname == null || !byName.TryGetValue(pname, out var parent)) break;
            if (!seen.Add(parent.Name)) break;
            if (IsGive(parent)) found.Add(parent);
            if (parent.ExportType.StartsWith("QFT_Prompt", StringComparison.Ordinal) ||
                parent.ExportType.Contains("Choice"))
            {
                if (++promptsCrossed >= 2) break;   // left the completion beat
            }
            cur = parent;
        }

        // forward: BFS over OutputConnections
        var queue = new Queue<(UObject node, int depth)>();
        queue.Enqueue((completeNode, 0));
        var fseen = new HashSet<string>(StringComparer.Ordinal) { completeNode.Name };
        while (queue.Count > 0)
        {
            var (node, depth) = queue.Dequeue();
            if (depth >= 8) continue;
            var outs = node.GetOrDefault<FGuid[]>("OutputConnections");
            if (outs == null) continue;
            foreach (var g in outs)
            {
                if (!byGuid.TryGetValue(g, out var next)) continue;
                if (!fseen.Add(next.Name)) continue;
                if (IsGive(next) && !found.Contains(next)) found.Add(next);
                // don't cross into a new dialogue beat going forward either
                if (next.ExportType.StartsWith("QFT_Prompt", StringComparison.Ordinal) ||
                    next.ExportType.Contains("Choice")) continue;
                queue.Enqueue((next, depth + 1));
            }
        }
        return found;
    }

    static string PidForItem(DefaultFileProvider provider, Dictionary<string, string> contentIndex,
        Dictionary<string, string> namePid, Dictionary<string, string> cache, string assetName, string objectPath)
    {
        if (assetName == null) return null;
        if (cache.TryGetValue(assetName, out var hit)) return hit;
        string pid = null;
        if (namePid.TryGetValue(assetName, out var fromDump)) pid = fromDump;
        if (pid == null && objectPath != null)
        {
            // static fallback: read PersistenceID off the item asset itself
            var pkgKey = ItemIconDiscovery.ResolvePackagePath(contentIndex, objectPath);
            if (pkgKey != null)
            {
                try
                {
                    foreach (var exp in provider.LoadPackage(pkgKey).GetExports())
                    {
                        var p = exp.GetOrDefault<string>("PersistenceID");
                        if (p != null) { pid = p; break; }
                    }
                }
                catch { }
            }
        }
        cache[assetName] = pid;
        return pid;
    }

    static string ObjPath(CUE4Parse.UE4.Objects.UObject.FPackageIndex idx)
    {
        try { return idx?.ResolvedObject?.GetPathName(); } catch { return null; }
    }

    static void AddRewards(DefaultFileProvider provider, Dictionary<string, string> contentIndex,
        Dictionary<string, string> namePid, Dictionary<string, string> cache, UObject give, QuestEntry quest)
    {
        void Add(string asset, string objectPath, int count, string type)
        {
            if (asset == null && type == "item") return;
            if (quest.rewards.Any(r => r.asset == asset)) return;   // alternate completion paths repeat rewards
            quest.rewards.Add(new RewardEntry
            {
                item_id = type == "item" ? PidForItem(provider, contentIndex, namePid, cache, asset, objectPath) : null,
                asset = asset,
                count = count,
                type = type,
            });
        }

        switch (give.ExportType)
        {
            case "QFT_GiveItemToPlayer_C":
            {
                var item = give.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex>("ItemData");
                Add(ObjName(item), ObjPath(item), give.GetOrDefault<int>("Amount", 1), "item");
                break;
            }
            case "QFT_GiveItemsToPlayer_C":
            {
                var arr = give.GetOrDefault<CUE4Parse.UE4.Assets.Objects.FStructFallback[]>("ItemData");
                if (arr != null)
                    foreach (var s in arr)
                    {
                        var item = s.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex>("ItemData");
                        var amount = s.GetOrDefault<int>("Amount", s.GetOrDefault<int>("Count", 1));
                        Add(ObjName(item), ObjPath(item), amount, "item");
                    }
                break;
            }
            case "QFT_GiveCraftingRecipe_C":
            {
                // ArrayProperty literally named "Summon Item Recipes" of RecipeData refs.
                var recipes = give.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex[]>("Summon Item Recipes");
                if (recipes != null)
                    foreach (var r in recipes)
                    {
                        var asset = ObjName(r);
                        if (asset == null) continue;
                        if (quest.rewards.Any(x => x.asset == asset)) continue;
                        quest.rewards.Add(new RewardEntry
                        {
                            // RecipeData assets carry the same PersistenceID str
                            // property; that id is what RecipesUnlocked stores.
                            item_id = PidForItem(provider, contentIndex, namePid, cache, asset, ObjPath(r)),
                            asset = asset,
                            count = 1,
                            type = "recipe_unlock",
                        });
                    }
                break;
            }
            case "QFT_UnlockMount_C":
            {
                // SoftObjectProperty literally named "Mount ToUnlock"
                var soft = give.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FSoftObjectPath>("Mount ToUnlock");
                var apn = soft.AssetPathName.Text;
                string asset = null;
                if (!string.IsNullOrEmpty(apn) && apn != "None")
                {
                    var dot = apn.LastIndexOf('.');
                    asset = dot >= 0 ? apn.Substring(dot + 1) : apn;
                }
                Add(asset ?? "UnknownMount", null, 1, "mount_unlock");
                break;
            }
        }
    }

    static List<string> FindQuestFlowPackages(DefaultFileProvider provider)
    {
        return provider.Files.Keys
            .Where(k => k.EndsWith(".uasset", StringComparison.OrdinalIgnoreCase))
            .Where(k =>
            {
                var norm = k.Replace('\\', '/');
                if (norm.IndexOf("Gameplay/Quests", StringComparison.OrdinalIgnoreCase) < 0) return false;
                var name = Path.GetFileNameWithoutExtension(norm);
                return name.StartsWith("QF_", StringComparison.OrdinalIgnoreCase);
            })
            .OrderBy(k => k, StringComparer.OrdinalIgnoreCase)
            .ToList();
    }

    static string ObjName(CUE4Parse.UE4.Objects.UObject.FPackageIndex idx)
    {
        try { return idx?.ResolvedObject?.Name.Text; } catch { return null; }
    }

    // Survey: for every QF_* package print which quests it gives/completes and
    // which items it gives -- to design reward attribution.
    static void SurveyQuestFlows(DefaultFileProvider provider)
    {
        foreach (var pkgPath in FindQuestFlowPackages(provider))
        {
            List<string> lines = new List<string>();
            try
            {
                var pkg = provider.LoadPackage(pkgPath);
                foreach (var exp in pkg.GetExports())
                {
                    var t = exp.ExportType;
                    if (t == "QFT_CompleteQuest_C" || t == "QFT_CompleteQuest_RestlessGhost_C")
                    {
                        var q = exp.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex>("QuestData");
                        lines.Add($"  COMPLETE {ObjName(q)}");
                    }
                    else if (t == "QFT_CompleteQuests_C")
                    {
                        var arr = exp.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex[]>("QuestData");
                        if (arr != null) foreach (var q in arr) lines.Add($"  COMPLETE(multi) {ObjName(q)}");
                    }
                    else if (t == "QFT_GiveQuest_C")
                    {
                        var q = exp.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex>("QuestData");
                        lines.Add($"  GIVEQUEST {ObjName(q)}");
                    }
                    else if (t == "QFT_GiveItemToPlayer_C")
                    {
                        var item = exp.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex>("ItemData");
                        var amount = exp.GetOrDefault<int>("Amount", 1);
                        lines.Add($"  GIVEITEM {ObjName(item)} x{amount}");
                    }
                    else if (t == "QFT_GiveItemsToPlayer_C")
                    {
                        var arr = exp.GetOrDefault<CUE4Parse.UE4.Assets.Objects.FStructFallback[]>("ItemData");
                        if (arr != null)
                            foreach (var s in arr)
                            {
                                var item = s.GetOrDefault<CUE4Parse.UE4.Objects.UObject.FPackageIndex>("ItemData");
                                var amount = s.GetOrDefault<int>("Amount", s.GetOrDefault<int>("Count", 1));
                                lines.Add($"  GIVEITEMS {ObjName(item)} x{amount}");
                            }
                    }
                    else if (t == "QFT_UnlockMount_C")
                    {
                        lines.Add($"  UNLOCKMOUNT");
                    }
                }
            }
            catch (Exception ex)
            {
                lines.Add($"  ERROR {ex.Message}");
            }
            if (lines.Count > 0)
            {
                Console.WriteLine(pkgPath);
                foreach (var l in lines) Console.WriteLine(l);
            }
        }
    }
}
