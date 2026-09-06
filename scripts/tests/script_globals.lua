-- Run inside the actual secureStandardGlobals factory, not JsePlatform defaults.
-- Start with a real string.* call so the unfixed factory reproduces the nil-index error.
assert(string.format("%s %.1f %02d", "heat", 12.5, 3) == "heat 12.5 03")
assert(type(string) == "table")
assert(package.loaded.string == string)
assert(require("string") == string)

-- Both global functions and the shared string metatable must work.
assert(string.sub("tacz", 2, -2) == "ac")
assert(string.sub("tacz", 8) == "")
assert(("MAG %02d"):format(7) == "MAG 07")
assert(("tacz"):sub(2, 3) == "ac")
assert(string.lower("TaCZ") == "tacz")
assert(string.upper("TaCZ") == "TACZ")
assert(string.len("tacz") == 4)
assert(string.rep("ab", 3) == "ababab")
assert(string.reverse("tacz") == "zcat")
local first, last = string.find("gun:ak47", "ak%d+")
assert(first == 5 and last == 8)
assert(string.match("gun:ak47", "gun:(%w+)") == "ak47")
local replaced, count = string.gsub("ak47-ak74", "ak", "AK")
assert(replaced == "AK47-AK74" and count == 2)
local words = {}
for word in string.gmatch("one two", "%w+") do
    table.insert(words, word)
end
assert(table.concat(words, ":") == "one:two")
local a, b = string.byte("ab", 1, 2)
assert(a == 97 and b == 98)
assert(string.char(a, b) == "ab")
assert(load(string.dump(function() return 42 end))() == 42)

-- Existing libraries, bytecode loading and preloaded gun-pack-style modules remain usable.
assert(math.floor(3.75) == 3)
assert(bit32.band(7, 3) == 3)
assert(type(load) == "function" and type(pcall) == "function")
assert(package.loaded.regression_module == nil)
local loads = 0
package.preload.regression_module = function()
    loads = loads + 1
    return { label = ("gun:%s"):format("ak47") }
end
local module = require("regression_module")
assert(module.label == "gun:ak47")
assert(require("regression_module") == module and loads == 1)

-- Do not accidentally replace the curated factory with JsePlatform.standardGlobals().
-- Absence of these libraries is NOT a claim of a complete security sandbox.
for _, name in ipairs({"coroutine", "io", "os", "luajava", "debug"}) do
    assert(_G[name] == nil, "Unexpected global library: " .. name)
    assert(package.loaded[name] == nil, "Unexpected loaded library: " .. name)
end

-- Recreating Globals must not reuse a previous manager's globals/package tables.
assert(_G.regression_marker == nil)
_G.regression_marker = true
