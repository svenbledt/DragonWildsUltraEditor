-- ItemDumper - UE4SS Lua mod for RuneScape: Dragonwilds  (v2, crash-safe)
-- Dumps item-data objects (PersistenceID + item fields) to a JSONL file so the
-- DragonWilds Ultra Editor's item_ids.py can be regenerated after a game update.
--
-- v1 hard-crashed the game: it swept broad base classes (DataAsset /
-- PrimaryDataAsset) and reflectively read every property of thousands of
-- unrelated objects. UE4SS reads raw object memory there, so a single bad
-- deref is a NATIVE access violation that pcall cannot catch.
--
-- v2 is defensive:
--   * only enumerates the exact item-data class discovered from your inventory
--     (no base-class sweep, no ForEachProperty),
--   * reads a fixed, known set of fields (guarded),
--   * writes checkpoints to disk at every step and a per-object progress marker
--     BEFORE each read, so if it still crashes we know the exact culprit,
--   * writes items incrementally and flushes, so partial output survives.
--
-- Usage: load into a world with items in your inventory, then press F8
-- (or console: dump_items). Output in …\Binaries\Win64\ue4ss\ :
--   ItemDumper_items.jsonl        one JSON object per item (incremental)
--   ItemDumper_diagnostics.txt    milestone checkpoints
--   ItemDumper_progress.txt       last object touched (crash pointer)

local UEHelpers = require("UEHelpers")

local MOD_NAME  = "ItemDumper"
local OUT_FILE  = "ItemDumper_items.jsonl"
local DIAG_FILE = "ItemDumper_diagnostics.txt"
local PROG_FILE = "ItemDumper_progress.txt"

-- Fields we try to read off each item-data object. Kept small on purpose.
local FIELDS = {
    "SourceString", "PersistenceID", "Weight", "Durability", "MaxStackSize",
    "VitalShield", "IconFile", "Category", "PowerLevel", "DisplayName",
    "ItemName", "Name", "MaxStack", "Icon", "Description",
}

local function log(msg)
    print(string.format("[%s] %s\n", MOD_NAME, tostring(msg)))
end

-- checkpoint: append + close so it is on disk even if the process dies next line
local function ck(msg)
    local f = io.open(DIAG_FILE, "a")
    if f then f:write(tostring(msg) .. "\n"); f:close() end
end

-- progress: overwrite; last object we were about to touch
local function prog(msg)
    local f = io.open(PROG_FILE, "w")
    if f then f:write(tostring(msg) .. "\n"); f:close() end
end

local function safe(f)
    local ok, v = pcall(f)
    if ok then return v end
    return nil
end

-- Reduce a UE property value to a Lua scalar. Only strings/numbers/bools pass
-- through directly; for userdata we make ONE guarded ToString attempt.
local function scalarize(v)
    local t = type(v)
    if t == "string" or t == "number" or t == "boolean" then return v end
    if t == "nil" then return nil end
    local s = safe(function() return v:ToString() end)
    if type(s) == "string" and #s > 0 then return s end
    return nil
end

local function tryGet(obj, name)
    return safe(function() return obj[name] end)
end

local function jsonEscape(s)
    s = tostring(s)
    s = s:gsub("\\", "\\\\"):gsub('"', '\\"')
    s = s:gsub("\n", "\\n"):gsub("\r", "\\r"):gsub("\t", "\\t")
    return s
end

local function jsonValue(v)
    local t = type(v)
    if t == "number" then
        if v == math.floor(v) and math.abs(v) < 1e15 then
            return string.format("%d", v)
        end
        return tostring(v)
    elseif t == "boolean" then
        return v and "true" or "false"
    elseif t == "nil" then
        return "null"
    else
        return '"' .. jsonEscape(v) .. '"'
    end
end

local function readRecord(obj)
    local rec = {}
    for _, f in ipairs(FIELDS) do
        local sv = scalarize(tryGet(obj, f))
        if sv ~= nil then rec[f] = sv end
    end
    local cn = safe(function() return obj:GetClass():GetFName():ToString() end)
    if cn then rec.__class = cn end
    -- asset path (e.g. ...ItemData_SteelSword.0) - a language-neutral fallback
    -- name for brand-new items, since the Name property is localized.
    local fn = safe(function() return obj:GetFullName() end)
    if fn then rec.__fullname = fn end
    return rec
end

local function recordToJson(rec)
    local parts = {}
    for k, v in pairs(rec) do
        table.insert(parts, '"' .. jsonEscape(k) .. '":' .. jsonValue(v))
    end
    return "{" .. table.concat(parts, ",") .. "}"
end

-- Generic base classes we must never sweep (thousands of unrelated objects -> crash)
local GENERIC = {
    DominionDataAsset = true, DataAsset = true,
    PrimaryDataAsset = true, Object = true,
}

-- Walk an object's class chain, returning the item/recipe-specific class names
-- (leaf .. up to, but excluding, the generic bases above).
local function classChainNames(obj)
    local names = {}
    safe(function()
        local c = obj:GetClass()
        while c and c:IsValid() do
            local nm = c:GetFName():ToString()
            if GENERIC[nm] then break end
            names[#names + 1] = nm
            c = c:GetSuperStruct()
        end
    end)
    return names
end

-- ===== Recipe dump (crash-safe) =======================================
-- Recipes are their own asset class (separate id namespace from items).
-- IMPORTANT: never read a UObject reference off another object and call a
-- method (GetClass/GetSuperStruct/etc.) on it. Dereferencing a *referenced*
-- UObject is a NATIVE access violation that pcall cannot catch - that is what
-- crashed the game (reading the recipe pointer off a RecipeUnlocker consumable).
-- We ONLY use FindAllOf on candidate class names and read POD fields off the
-- objects we get back - exactly what the item dump does, which is proven safe.
local RECIPE_OUT = "ItemDumper_recipes.jsonl"
local RECIPE_CLASS_CANDIDATES = {
    "RecipeData", "CraftingRecipeData", "DominionRecipeData", "RecipeDataAsset",
    "CraftingRecipe", "BuildingRecipeData", "CookingRecipeData", "ItemRecipeData",
    "RecipeItemData", "UnlockableRecipeData", "CraftingRecipeDataAsset",
    "DA_RecipeData", "RecipeDefinition", "Recipe",
}

local function dumpRecipes()
    ck("=== recipe dump (class-name scan, crash-safe) ===")
    local out = io.open(RECIPE_OUT, "w")
    if not out then ck("cannot open " .. RECIPE_OUT); return end
    local kept, seen = 0, {}
    for _, tname in ipairs(RECIPE_CLASS_CANDIDATES) do
        local arr = safe(function() return FindAllOf(tname) end)
        local n = (type(arr) == "table") and #arr or 0
        ck("  FindAllOf(" .. tname .. ") = " .. n)
        for i = 1, n do
            local o = arr[i]
            local fn = safe(function() return o:GetFullName() end)
            prog("recipe " .. tname .. " " .. i .. "/" .. n .. "  " .. tostring(fn))
            if o and safe(function() return o:IsValid() end) then
                local key = fn or tostring(o)
                if not seen[key] then
                    local pid = scalarize(tryGet(o, "PersistenceID"))
                    if pid ~= nil then
                        seen[key] = true
                        out:write(recordToJson(readRecord(o)) .. "\n")
                        out:flush()
                        kept = kept + 1
                    end
                end
            end
        end
    end
    out:close()
    ck("recipe DONE: " .. kept .. " records -> " .. RECIPE_OUT)
    log("dumped " .. kept .. " recipe records -> " .. RECIPE_OUT)
end

-- ===== Mount dump ======================================================
-- Mounts are unlocked in the save via Character.Mount.MountsUnlockedList, which
-- stores per-variant refs like "MountDataAsset:DA_Mount_Terrorbird_00_00" plus a
-- type tag like "TAG.Mounts.Type.Terrorbird". So the real objects to enumerate
-- are the MountDataAsset assets (NOT the ConsumableMountUnlocker consumables,
-- whose asset numbering doesn't match). We record each mount's full name; the
-- converter builds the exact "MountDataAsset:<assetname>" unlock strings from it.
local MOUNT_OUT = "ItemDumper_mounts.jsonl"
local MOUNT_UNLOCKER_CLASSES = { "MountDataAsset", "ConsumableMountUnlocker" }
local MOUNT_TAG_PROPS = {
    "MountToUnlock", "MountTag", "MountType", "MountTypeTag", "Mount",
    "GrantedMount", "UnlockMountTag", "MountToGrant", "MountIdentifier",
    "MountId", "MountName", "MountGameplayTag", "GameplayTag", "Tag",
}

-- Pull a readable tag string out of a value that may be a plain string, an FName,
-- or an FGameplayTag struct (whose useful field is TagName).
local function tagString(v)
    if v == nil then return nil end
    local s = scalarize(v)
    if type(s) == "string" and #s > 0 then return s end
    if type(v) == "userdata" then
        local tn = scalarize(tryGet(v, "TagName"))
        if type(tn) == "string" and #tn > 0 then return tn end
        local gt = tryGet(v, "GameplayTag")
        if gt ~= nil then
            local tn2 = scalarize(tryGet(gt, "TagName"))
            if type(tn2) == "string" and #tn2 > 0 then return tn2 end
        end
    end
    return nil
end

local function dumpMounts()
    ck("=== mount dump ===")
    local out = io.open(MOUNT_OUT, "w")
    if not out then ck("cannot open " .. MOUNT_OUT); return end
    local kept = 0
    for _, cls in ipairs(MOUNT_UNLOCKER_CLASSES) do
        local arr = safe(function() return FindAllOf(cls) end)
        if type(arr) == "table" then
            ck("  FindAllOf(" .. cls .. ")=" .. #arr)
            for i = 1, #arr do
                local o = arr[i]
                local fn = safe(function() return o:GetFullName() end)
                prog("mount " .. cls .. " " .. i .. "/" .. #arr .. "  " .. tostring(fn))
                if o and safe(function() return o:IsValid() end) then
                    local rec = { __class = cls }
                    if fn then rec.__fullname = fn end
                    local pid = scalarize(tryGet(o, "PersistenceID"))
                    if pid ~= nil then rec.PersistenceID = pid end
                    -- record every candidate mount-tag property that yields a string
                    for _, pn in ipairs(MOUNT_TAG_PROPS) do
                        local ts = tagString(tryGet(o, pn))
                        if ts ~= nil then rec[pn] = ts end
                    end
                    out:write(recordToJson(rec) .. "\n")
                    out:flush()
                    kept = kept + 1
                end
            end
        end
    end
    out:close()
    ck("mount DONE: " .. kept .. " records -> " .. MOUNT_OUT)
    log("dumped " .. kept .. " mount records -> " .. MOUNT_OUT)
end

-- ===== Building dump (crash-safe) =====================================
-- Build pieces are unlocked in the save via Progress.BuildingsUnlocked - a
-- SEPARATE id namespace from items AND recipes (verified: zero overlap). Like
-- the recipe dump this is a pure class-name scan: we only FindAllOf candidate
-- class names and read POD fields (PersistenceID, full name) off the returned
-- objects; we NEVER dereference a referenced UObject (that is the uncatchable
-- native crash). We deliberately do NOT sweep DominionDataAsset/DataAsset - that
-- crashed v1. We scan many likely names; whichever exist get dumped (deduped by
-- full name), and the converter confirms the real building class by overlap with
-- your saves' BuildingsUnlocked, so an accidental non-building match is harmless.
local BUILDING_OUT = "ItemDumper_buildings.jsonl"
local BUILDING_CLASS_CANDIDATES = {
    "BuildingPieceData", "BuildingData", "BuildingPieceDataAsset",
    "DominionBuildingPieceData", "DominionBuildingData", "BuildableData",
    "BuildPieceData", "ConstructionData", "ConstructionPieceData",
    "StructureData", "StructurePieceData", "PlaceableData", "PlaceableItemData",
    "BuildingCategoryData", "BuildableRecipeData", "BuildingRecipeData",
    "ConstructionRecipeData", "HammerRecipeData", "BuildMenuData",
    "BuildingPiece", "Buildable", "Building",
}

local function dumpBuildings()
    ck("=== building dump (class-name scan, crash-safe) ===")
    local out = io.open(BUILDING_OUT, "w")
    if not out then ck("cannot open " .. BUILDING_OUT); return end
    local kept, seen = 0, {}
    for _, tname in ipairs(BUILDING_CLASS_CANDIDATES) do
        local arr = safe(function() return FindAllOf(tname) end)
        local n = (type(arr) == "table") and #arr or 0
        ck("  FindAllOf(" .. tname .. ") = " .. n)
        for i = 1, n do
            local o = arr[i]
            local fn = safe(function() return o:GetFullName() end)
            prog("building " .. tname .. " " .. i .. "/" .. n .. "  " .. tostring(fn))
            if o and safe(function() return o:IsValid() end) then
                local key = fn or tostring(o)
                if not seen[key] then
                    local pid = scalarize(tryGet(o, "PersistenceID"))
                    if pid ~= nil then
                        seen[key] = true
                        out:write(recordToJson(readRecord(o)) .. "\n")
                        out:flush()
                        kept = kept + 1
                    end
                end
            end
        end
    end
    out:close()
    ck("building DONE: " .. kept .. " records -> " .. BUILDING_OUT)
    log("dumped " .. kept .. " building records -> " .. BUILDING_OUT)
end

-- ===== Sanguine Urn / shrine dump (crash-safe) =========================
-- Lifepool-expanding "Sanguine Urns" are tracked in the save via
-- Progress.ShrinesUnlocked - 32-char uppercase hex FGuids (level-actor
-- persistence ids), a SEPARATE namespace from item/recipe/building PIDs.
-- We do a pure class-name scan (FindAllOf + POD reads only, never deref a
-- referenced UObject) over candidate shrine/urn data-asset classes. Whichever
-- exist get dumped, deduped by full name. build_shrine_ids.py then validates
-- the result against the known GUIDs harvested from real saves.
local URN_OUT = "ItemDumper_urns.jsonl"
local URN_CLASS_CANDIDATES = {
    "SanguineUrnData", "ShrineData", "HealthShrineData", "LifePoolShrineData",
    "LifeShrineData", "ShrineDataAsset", "InteractableShrineData", "SanguineUrn",
    "HealthUpgradeData", "MaxHealthShrineData", "VitalityShrineData",
}

local function dumpUrns()
    ck("=== urn/shrine dump (class-name scan, crash-safe) ===")
    local out = io.open(URN_OUT, "w")
    if not out then ck("cannot open " .. URN_OUT); return end
    local kept, seen = 0, {}
    for _, tname in ipairs(URN_CLASS_CANDIDATES) do
        local arr = safe(function() return FindAllOf(tname) end)
        local n = (type(arr) == "table") and #arr or 0
        ck("  FindAllOf(" .. tname .. ") = " .. n)
        for i = 1, n do
            local o = arr[i]
            local fn = safe(function() return o:GetFullName() end)
            prog("urn " .. tname .. " " .. i .. "/" .. n .. "  " .. tostring(fn))
            if o and safe(function() return o:IsValid() end) then
                local key = fn or tostring(o)
                if not seen[key] then
                    local pid = scalarize(tryGet(o, "PersistenceID"))
                    if pid ~= nil then
                        seen[key] = true
                        out:write(recordToJson(readRecord(o)) .. "\n")
                        out:flush()
                        kept = kept + 1
                    end
                end
            end
        end
    end
    out:close()
    ck("urn DONE: " .. kept .. " records -> " .. URN_OUT)
    log("dumped " .. kept .. " urn/shrine records -> " .. URN_OUT)
end

-- ===== Sanguine Urn ACTOR discovery sweep (opt-in, F7) =================
-- The 7 known urn GUIDs are a PARTIAL set; the game has MORE urns whose ids we
-- don't know. Those ids are PLACED-ACTOR persistence GUIDs baked into the level
-- (World Partition), NOT data assets - every urn data-asset class returns
-- FindAllOf==0, so the F8 dump can never emit them. To learn the complete set we
-- first need the urn ACTOR's blueprint class name + which property holds its
-- persistence FGuid. This sweep discovers both. It is CRASH-SAFE the same way the
-- rest of the mod is: it reads only each actor's OWN class name (proven safe over
-- 1392 items) and, for actors whose class name looks urn/shrine-ish, reads a fixed
-- set of GUID/state properties DIRECTLY off the actor. It NEVER calls a method on
-- a referenced UObject (component/pointer) - that is the uncatchable native crash.
-- Usage: load into a WORLD, stand next to any Sanguine Urn (locked or unlocked),
-- press F7 (or console: discover_urns). Output: ItemDumper_urn_discovery.txt
local DISC_OUT = "ItemDumper_urn_discovery.txt"
local URN_KEYWORDS = {
    "urn", "shrine", "sanguine", "sanguin", "bloodpool", "lifepool",
    "vital", "altar", "lifeshrine", "healthshrine", "obelisk", "font",
}
-- The two FGuid StructProperties discovered on BP_HealthShrine_C's schema are
-- listed FIRST: UniqueShrineIdentifier (HealthShrine base) and SpudGuid
-- (WorldActor base; SPUD = Steve's Persistent Unreal Data save plugin). One of
-- these is the value stored in Progress.ShrinesUnlocked. Both are safe POD
-- (FGuid) reads. The rest are legacy guesses, harmless if absent.
local GUID_PROPS = {
    "UniqueShrineIdentifier", "SpudGuid",
    "PersistentGuid", "PersistenceGuid", "PersistentId", "PersistenceId",
    "PersistenceID", "ActorGuid", "ActorGUID", "Guid", "GUID", "SaveGuid",
    "SaveGUID", "SavedGuid", "UniqueId", "UniqueID", "Id", "ID", "ShrineGuid",
    "ShrineId", "ShrineID", "UrnGuid", "UrnId", "PersistentActorGuid", "MyGuid",
    "ObjectGuid", "PersistenceGUID", "StableGuid", "LevelActorGuid", "WorldTag",
}
local STATE_PROPS = {
    "bActivated", "bUnlocked", "bCollected", "bIsActivated", "bConsumed",
    "Activated", "bInteracted", "bUsed", "bIsUnlocked", "bHasBeenActivated",
}
local KNOWN_URN_GUIDS = {
    ["824A3798412A1067890E86A2AEB609FF"] = true,
    ["DB621D2A40316F7B97255696742C2AA1"] = true,
    ["7DE4A84C4997053BD7171089B408AE13"] = true,
    ["485514AA4D440FC3EBF331B6F5128ECE"] = true,
    ["DCF55CC14E4019584B5B03AB1D1ECC75"] = true,
    ["13A95FDF40A30E7465E66C96CAA63778"] = true,
    ["BA041CF14868F751575411B22EFE218A"] = true,
    ["186B64E241A3790BE54292A84653E981"] = true,  -- confirmed via in-game unlock
}

local function u32hex(x)
    if type(x) ~= "number" then return nil end
    x = math.floor(x)
    if x < 0 then x = x + 4294967296 end
    return string.format("%08X", x)
end

-- Reconstruct the 32-hex ShrinesUnlocked form from an FGuid's A/B/C/D (POD ints).
local function guidFromStruct(v)
    if type(v) ~= "userdata" then return nil end
    local a = u32hex(tryGet(v, "A"))
    local b = u32hex(tryGet(v, "B"))
    local c = u32hex(tryGet(v, "C"))
    local d = u32hex(tryGet(v, "D"))
    if a and b and c and d then return a .. b .. c .. d end
    return nil
end

local function nameMatches(cn)
    local l = (type(cn) == "string") and cn:lower() or ""
    for _, kw in ipairs(URN_KEYWORDS) do
        if l:find(kw, 1, true) then return true end
    end
    return false
end

-- Stop the schema walk at these bases (Actor/Object carry huge, irrelevant
-- property sets; the urn's persistence GUID lives on the BP or a nearer C++ base).
local SCHEMA_STOP = {
    Actor = true, Object = true, DominionDataAsset = true, DataAsset = true,
    PrimaryDataAsset = true,
}

-- Enumerate a matched actor's OWN + inherited (up to Actor) property schema:
-- property NAME : TYPE only. We deliberately do NOT read any property value here:
-- reading an arbitrary property value off a live actor can be a native access
-- violation that pcall cannot catch (a component/delegate/object pointer) - that
-- is what crashed the F7 sweep. Reflection metadata (names/types via
-- ForEachProperty) is safe. Once the FGuid property is identified by name+type
-- from this list, GUID_PROPS reads only that ONE known field on the next run.
-- Output is flushed per line so a crash still leaves the partial schema on disk.
local function dumpActorSchema(o, out)
    out:write("    -- property schema (name : type), values NOT read --\n")
    out:flush()
    local cls = safe(function() return o:GetClass() end)
    local walked = {}
    while cls and safe(function() return cls:IsValid() end) do
        local cname = safe(function() return cls:GetFName():ToString() end) or "?"
        if SCHEMA_STOP[cname] or walked[cname] then break end
        walked[cname] = true
        out:write("    [" .. cname .. "]\n"); out:flush()
        prog("urn-discovery schema: " .. cname)
        local lines = {}
        local ok = pcall(function()
            cls:ForEachProperty(function(prop)
                local pn = safe(function() return prop:GetFName():ToString() end)
                local pt = safe(function() return prop:GetClass():GetFName():ToString() end)
                lines[#lines + 1] = string.format("      %-34s : %s",
                    tostring(pn), tostring(pt))
            end)
        end)
        if ok then
            for _, ln in ipairs(lines) do out:write(ln .. "\n") end
        else
            out:write("      (ForEachProperty unavailable/errored on this class)\n")
        end
        out:flush()
        cls = safe(function() return cls:GetSuperStruct() end)
    end
end

local function discoverUrnActors()
    local out = io.open(DISC_OUT, "w")
    if not out then log("cannot open " .. DISC_OUT); return end
    out:write("=== Sanguine Urn ACTOR discovery sweep ===\n")
    prog("urn-discovery: FindAllOf(Actor)")
    local actors = safe(function() return FindAllOf("Actor") end)
    local n = (type(actors) == "table") and #actors or 0
    out:write("FindAllOf('Actor') = " .. n .. " actors\n")
    if n == 0 then
        out:write("\nNo actors loaded. Be IN A WORLD (not the main menu), near an urn.\n")
        out:close()
        log("urn-discovery: 0 actors - load into a world first")
        return
    end

    local classCounts, matches = {}, 0
    out:write("\n--- keyword-matching actors (urn/shrine/sanguine/vital/altar/...) ---\n")
    for i = 1, n do
        local o = actors[i]
        local cn = safe(function() return o:GetClass():GetFName():ToString() end)
        if cn then
            classCounts[cn] = (classCounts[cn] or 0) + 1
            if nameMatches(cn) then
                matches = matches + 1
                local fn = safe(function() return o:GetFullName() end)
                prog("urn-discovery match " .. matches .. ": " .. tostring(cn))
                out:write(string.format("\n[MATCH %d] class=%s\n  full=%s\n",
                    matches, cn, tostring(fn)))
                for _, pn in ipairs(GUID_PROPS) do
                    local raw = tryGet(o, pn)
                    if raw ~= nil then
                        local hx = guidFromStruct(raw)          -- POD A/B/C/D (safe)
                        local sv = nil
                        local t = type(raw)
                        if t == "string" or t == "number" then
                            sv = raw
                        elseif hx ~= nil then
                            -- only ToString a userdata we've confirmed is an FGuid
                            sv = safe(function() return raw:ToString() end)
                        end
                        if sv ~= nil or hx ~= nil then
                            local hit = ""
                            if hx and KNOWN_URN_GUIDS[hx] then
                                hit = "   *** MATCHES KNOWN URN ***"
                            elseif type(sv) == "string"
                                    and KNOWN_URN_GUIDS[sv:upper()] then
                                hit = "   *** MATCHES KNOWN URN ***"
                            end
                            out:write(string.format("    %-22s str:%s  abcd:%s%s\n",
                                pn, tostring(sv), tostring(hx), hit))
                        end
                    end
                end
                for _, pn in ipairs(STATE_PROPS) do
                    local sv = scalarize(tryGet(o, pn))
                    if sv ~= nil then
                        out:write(string.format("    %-22s %s\n", pn, tostring(sv)))
                    end
                end
                -- full property schema + FGuid value scan (finds the GUID field
                -- regardless of its name)
                dumpActorSchema(o, out)
            end
        end
        if i % 5000 == 0 then out:flush() end
    end

    out:write(string.format(
        "\n\n=== %d keyword-matching actors of %d total ===\n", matches, n))
    -- full distinct class-name list (names only = safe) so the urn class can be
    -- spotted by eye even if no keyword matched.
    out:write("\n--- ALL distinct actor class names (name  x count) ---\n")
    local names = {}
    for cn in pairs(classCounts) do names[#names + 1] = cn end
    table.sort(names)
    for _, cn in ipairs(names) do
        out:write(string.format("  %-52s x%d\n", cn, classCounts[cn]))
    end
    out:close()
    prog("urn-discovery done")
    log(string.format("urn-discovery: %d matches / %d actors -> %s",
        matches, n, DISC_OUT))
end

local function runDiscoverGuarded()
    ExecuteInGameThread(function()
        local ok, err = pcall(discoverUrnActors)
        if not ok then log("urn-discovery ERROR: " .. tostring(err)) end
    end)
end

-- ===== Sanguine Urn GUID accumulator (F6) ==============================
-- CONFIRMED end-to-end: the ShrinesUnlocked entry is BP_HealthShrine_C's
-- UniqueShrineIdentifier FGuid, reconstructed as %08X%08X%08X%08X of A/B/C/D
-- (matched a real save byte-for-byte). This targeted read is safe (POD FGuid).
-- World Partition only streams nearby cells, so we ACCUMULATE: each press unions
-- every currently-loaded shrine's id into ItemDumper_urns.jsonl (the same file
-- build_shrine_ids.py consumes). Roam every region, pressing F6, until the total
-- stops growing - that yields the complete urn set. Cumulative across sessions.
local SHRINE_GUID_OUT   = "ItemDumper_urns.jsonl"
local SHRINE_ACTOR_CLASS = "BP_HealthShrine_C"
local SHRINE_GUID_FIELD  = "UniqueShrineIdentifier"
local EMPTY_GUID = "00000000000000000000000000000000"

local function loadExistingShrineGuids()
    local set, count = {}, 0
    local f = io.open(SHRINE_GUID_OUT, "r")
    if not f then return set, 0 end
    for line in f:lines() do
        local hx = line:match('"PersistenceID"%s*:%s*"(%x+)"')
        if hx and #hx == 32 then
            hx = hx:upper()
            if not set[hx] then set[hx] = true; count = count + 1 end
        end
    end
    f:close()
    return set, count
end

local function accumulateShrines()
    local set, before = loadExistingShrineGuids()
    local arr = safe(function() return FindAllOf(SHRINE_ACTOR_CLASS) end)
    local n = (type(arr) == "table") and #arr or 0
    ck(string.format("shrine-accum: FindAllOf(%s)=%d (had %d)",
        SHRINE_ACTOR_CLASS, n, before))
    local added = 0
    for i = 1, n do
        local o = arr[i]
        prog("shrine-accum " .. i .. "/" .. n)
        if o and safe(function() return o:IsValid() end) then
            local hx = guidFromStruct(tryGet(o, SHRINE_GUID_FIELD))
            if hx and #hx == 32 and hx ~= EMPTY_GUID and not set[hx] then
                set[hx] = true
                added = added + 1
                ck("  + " .. hx)
            end
        end
    end
    local keys = {}
    for k in pairs(set) do keys[#keys + 1] = k end
    table.sort(keys)
    local out = io.open(SHRINE_GUID_OUT, "w")
    if out then
        for _, k in ipairs(keys) do
            out:write(string.format(
                '{"PersistenceID":"%s","__class":"%s"}\n', k, SHRINE_ACTOR_CLASS))
        end
        out:close()
    end
    log(string.format("shrine-accum: %d loaded, +%d new, %d total -> %s",
        n, added, #keys, SHRINE_GUID_OUT))
    ck(string.format("shrine-accum DONE: +%d new, %d total", added, #keys))
end

local function runAccumGuarded()
    ExecuteInGameThread(function()
        local ok, err = pcall(accumulateShrines)
        if not ok then log("shrine-accum ERROR: " .. tostring(err)) end
    end)
end

-- Find one item-data object from the player's inventory (to discover its class)
local function sampleItemData()
    ck("  get PlayerController")
    local pc = UEHelpers.GetPlayerController()
    if not pc or not safe(function() return pc:IsValid() end) then
        ck("  PlayerController invalid"); return nil
    end
    ck("  GetInventory")
    local inv = safe(function() return pc:GetInventory() end)
    if not inv or not safe(function() return inv:IsValid() end) then
        ck("  inventory invalid"); return nil
    end
    local maxc = safe(function() return inv.MaxSlotCount end)
    if type(maxc) ~= "number" or maxc <= 0 then maxc = 64 end
    ck("  scanning up to " .. maxc .. " slots")
    for i = 0, maxc - 1 do
        local item = safe(function() return inv:GetItemFromSlot(i) end)
        if item and safe(function() return item:IsValid() end) then
            local data = safe(function() return item.ItemData end)
            if data and safe(function() return data:IsValid() end) then
                ck("  found item in slot " .. i)
                return data
            end
        end
    end
    ck("  no item found in any slot")
    return nil
end

local function dumpAll()
    log("starting dump...")
    -- truncate diagnostics + progress
    local d = io.open(DIAG_FILE, "w"); if d then d:write("=== ItemDumper v2 run ===\n"); d:close() end
    prog("start")

    ck("phase: discover sample item class")
    local sample = sampleItemData()
    if not sample then
        ck("ABORT: no sample item. Be in a world with items in your inventory.")
        log("no sample item found - stand in a world with items, then retry.")
        return
    end

    local leaf = safe(function() return sample:GetClass():GetFName():ToString() end)
    ck("sample class (leaf): " .. tostring(leaf))
    ck("class chain:")
    safe(function()
        local c = sample:GetClass()
        while c and c:IsValid() do
            ck("  " .. c:GetFName():ToString())
            c = c:GetSuperStruct()
        end
    end)
    ck("sample record: " .. recordToJson(readRecord(sample)))

    if not leaf then
        ck("ABORT: could not resolve leaf class name.")
        return
    end

    -- Build the list of classes to enumerate: walk the sample's class chain from
    -- the leaf up to (but NOT including) the generic base classes. This yields
    -- the item-specific classes only - e.g. HeldEquipmentData, EquipmentData,
    -- ItemData - and FindAllOf('ItemData') returns every item subclass instance
    -- (consumables, resources, armor, ...) for the complete set. We deliberately
    -- stop at DominionDataAsset/DataAsset: sweeping those in v1 caused a native
    -- crash because they contain thousands of unrelated data assets.
    local targets = classChainNames(sample)
    if #targets == 0 then targets = { leaf } end
    ck("target classes: " .. table.concat(targets, ", "))

    local out = io.open(OUT_FILE, "w")
    if not out then ck("ABORT: cannot open " .. OUT_FILE); return end

    local kept, seen = 0, {}
    for _, tname in ipairs(targets) do
        ck("phase: FindAllOf('" .. tname .. "')")
        local arr = safe(function() return FindAllOf(tname) end)
        if type(arr) ~= "table" then
            ck("  FindAllOf returned no table for " .. tname)
        else
            ck("  count: " .. #arr)
            for i = 1, #arr do
                local o = arr[i]
                local fn = safe(function() return o:GetFullName() end)
                prog(tname .. " " .. i .. " / " .. #arr .. "  " .. tostring(fn))
                if o and safe(function() return o:IsValid() end) then
                    local key = fn or tostring(o)
                    if not seen[key] then
                        local pid = scalarize(tryGet(o, "PersistenceID"))
                        if pid ~= nil then
                            seen[key] = true
                            out:write(recordToJson(readRecord(o)) .. "\n")
                            out:flush()
                            kept = kept + 1
                        end
                    end
                end
            end
        end
    end
    out:close()
    prog("done: " .. kept .. " records")
    ck("DONE: wrote " .. kept .. " unique records to " .. OUT_FILE)
    log(string.format("dumped %d records -> %s", kept, OUT_FILE))

    -- also dump recipes (separate asset class / id namespace)
    local ok, err = pcall(dumpRecipes)
    if not ok then ck("recipe dump ERROR: " .. tostring(err)) end

    -- and mount tags (from the mount-unlocker consumables)
    local okm, errm = pcall(dumpMounts)
    if not okm then ck("mount dump ERROR: " .. tostring(errm)) end

    -- and buildings (separate asset class / id namespace)
    local okb, errb = pcall(dumpBuildings)
    if not okb then ck("building dump ERROR: " .. tostring(errb)) end

    -- and Sanguine Urns: accumulate every loaded BP_HealthShrine_C's real
    -- UniqueShrineIdentifier GUID (cumulative). The old data-asset dumpUrns()
    -- always returned 0 (urns are level actors, not data assets) - superseded.
    local oku, erru = pcall(accumulateShrines)
    if not oku then ck("shrine-accum ERROR: " .. tostring(erru)) end
end

local function runGuarded()
    ExecuteInGameThread(function()
        local ok, err = pcall(dumpAll)
        if not ok then
            ck("LUA ERROR: " .. tostring(err))
            log("ERROR: " .. tostring(err))
        end
    end)
end

RegisterKeyBind(Key.F8, {}, runGuarded)
RegisterKeyBind(Key.F7, {}, runDiscoverGuarded)
RegisterKeyBind(Key.F6, {}, runAccumGuarded)

pcall(function()
    RegisterConsoleCommandHandler("dump_items", function()
        runGuarded()
        return true
    end)
end)
pcall(function()
    RegisterConsoleCommandHandler("discover_urns", function()
        runDiscoverGuarded()
        return true
    end)
end)
pcall(function()
    RegisterConsoleCommandHandler("dump_shrines", function()
        runAccumGuarded()
        return true
    end)
end)

log("Loaded (v2). In-world: F8 dumps items (+accumulates shrines); "
    .. "F6 (dump_shrines) accumulates loaded Sanguine-urn GUIDs as you roam; "
    .. "F7 (discover_urns) is the urn-actor discovery sweep.")
