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

    -- and Sanguine Urns / lifepool shrines (separate id namespace)
    local oku, erru = pcall(dumpUrns)
    if not oku then ck("urn dump ERROR: " .. tostring(erru)) end
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

pcall(function()
    RegisterConsoleCommandHandler("dump_items", function()
        runGuarded()
        return true
    end)
end)

log("Loaded (v2). In-world, press F8 (or console: dump_items) to dump the item list.")
