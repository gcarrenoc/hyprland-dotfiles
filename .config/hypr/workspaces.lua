-- NOTE: Hyprland only auto-reloads hyprland.lua. After editing this file run: hyprctl reload
-- Workspaces as a row (like GNOME / macOS Spaces) — empty ones disappear (like GNOME).
--
-- The model:
--   • The row is workspaces 1 … N (N ≤ 10), kept alive with persistent workspace
--     rules, and shown on the bar.
--   • An empty workspace is removed as soon as you're not on it (the ones after it
--     shift down). The one you're on stays even when empty, so you can open
--     something there; leave it empty and it goes. There's always at least one.
--   • Adding: the + on the bar, or stepping / jumping / sending past the end,
--     adds ONE new workspace at the end.
--   • Removing by hand: Super+Ctrl+Q removes the current workspace; its windows move
--     to the previous one and the workspaces after it shift down (no gaps).
--   • N is remembered across logins (~/.cache/hypr-workspaces).
--   • Several screens: each workspace stays on its screen. Previous / next / carry / swap stay on
--     the screen you're on, a new one opens there, and nothing is renumbered (that would move
--     windows between screens). The persistent rules are off then: Hyprland would pull all their
--     workspaces to the screen with the focus. Empty workspaces go away by themselves.
--
-- Functions (global WS, so Waybar can call them via
-- `hyprctl dispatch 'function() WS.step(1) end'`):
--   WS.step(±1)   previous / next (next at the end = new)   Super+Ctrl+H/L, scroll, swipe
--   WS.go(n)      go to workspace n (past the end: one new one)  Super+1…0
--   WS.new()      add a workspace at the end and go there   + on the bar
--   WS.send(n)    send window to workspace n (past the end: one new one)  Super+Shift+1…0
--   WS.carry(±1)  take window to prev / next                Super+Ctrl+Shift+H/L
--   WS.swap(±1)   move this workspace left / right          Super+Alt+H/L
--   WS.insert(±1) new empty workspace left / right of this   Super+Ctrl+Alt+H/L
--   WS.remove()   remove the current workspace              Super+Ctrl+Q
--   WS.prune()    remove empty workspaces you're not on     automatic (window closed / moved, workspace changed)

local W = {}
local MAX = 10
local STATE = os.getenv("HOME") .. "/.cache/hypr-workspaces"

-- persistent rules for 1 … MAX, switched on for 1 … N
local rules = {}
for i = 1, MAX do
    rules[i] = hl.workspace_rule({ workspace = tostring(i), persistent = true, enabled = false })
end

local function read_count()
    local f = io.open(STATE, "r")
    local n = f and tonumber(f:read("*l")) or nil
    if f then f:close() end
    return math.max(1, math.min(n or 1, MAX))
end

local count = read_count()

local function save()
    local f = io.open(STATE, "w")
    if f then f:write(tostring(count), "\n"); f:close() end
end

local function current()
    local ws = hl.get_active_workspace()
    return ws and ws.id or 1, ws
end

local function windows_on(id) return hl.get_workspace_windows(id) or {} end

local function move_all(from, to)
    for _, w in ipairs(windows_on(from)) do
        hl.dispatch(hl.dsp.window.move({ window = "address:" .. w.address, workspace = to, follow = false }))
    end
end

local function focus(n) hl.dispatch(hl.dsp.focus({ workspace = n })) end

local busy = false

-- screens (a mirrored one isn't a screen of its own)
local function screens()
    local out = {}
    for _, m in ipairs(hl.get_monitors() or {}) do
        if not m.is_mirror and m.name ~= "FALLBACK" then out[#out + 1] = m end
    end
    return out
end
local function multi() return #screens() > 1 end

local function sync()
    local keep = not multi()                     -- several screens: see "The model"
    for i = 1, MAX do rules[i]:set_enabled(keep and i <= count) end
    save()
end

-- workspaces shown on some screen right now: never removed under your eyes
local function shown()
    local set = {}
    for _, m in ipairs(screens()) do
        if m.active_workspace then set[m.active_workspace.id] = true end
    end
    return set
end

-- highest workspace in use: with windows, or shown on a screen
local function top_used()
    local top, seen = 1, shown()
    for _, ws in ipairs(hl.get_workspaces()) do
        if not ws.special and ws.id and ws.id > 0 and (ws.windows > 0 or seen[ws.id]) and ws.id > top then top = ws.id end
    end
    return math.min(top, MAX)
end

-- the numbers of the row that belong to this screen, in order
local function row()
    local here, ws = current()
    if not multi() then
        local all = {}
        for i = 1, count do all[i] = i end
        return all
    end
    local mine, mon = {}, ws and ws.monitor and ws.monitor.name
    for _, w in ipairs(hl.get_workspaces()) do
        if not w.special and w.id and w.id > 0 and w.id <= count and w.monitor and w.monitor.name == mon then
            mine[#mine + 1] = w.id
        end
    end
    table.sort(mine)
    return mine
end

-- the workspace d steps away on this screen, or nil
local function neighbour(d)
    local here, r = current(), row()
    for k, id in ipairs(r) do
        if id == here then return r[k + d] end
    end
end

local function full()
    if multi() then count = top_used() end
    if count < MAX then return false end
    hl.exec_cmd("notify-send -a Workspaces -u low 'Maximum of 10 workspaces'")
    return true
end

-- safety: windows or screens that end up beyond the row (apps, rules, a new monitor…) extend it
function W.check()
    if busy then return end
    local top = top_used()
    if top > count then count = top; sync() end
end

local function last_and_empty()
    local here = current()
    return here == count and #windows_on(here) == 0
end

-- one new workspace at the end, on this screen (focus first: the persistent rule alone could
-- create it on another screen)
function W.new()
    if #windows_on(current()) == 0 and (multi() or last_and_empty()) then return end   -- already on an empty one
    if full() then return end
    count = count + 1
    focus(count)
    sync()
end

function W.go(n)                                -- Super+N; past the end: one new one
    if n <= count then focus(n) else W.new() end
end

-- show the workspace d steps away on this screen, only if it exists (dragging a file to a screen edge)
function W.flip(d)
    local target = neighbour(d)
    if target then focus(target) end
end

function W.step(d)
    local target = neighbour(d)
    if target then focus(target)
    elseif d > 0 then W.new() end
end

-- number of an existing workspace, or of one new one at the end
local function usable(n)
    if n <= count then return n end
    if full() then return nil end
    count = count + 1
    return count
end

local function move_window(opts, n)
    local target = usable(n)
    if not target or target == current() then return end
    opts.workspace = target
    hl.dispatch(hl.dsp.window.move(opts))
    sync()
end

function W.send(n) move_window({ follow = false }, n) end            -- Super+Shift+N

-- move a given window (by address) to workspace n without following it
function W.send_window(address, n) move_window({ window = "address:" .. address, follow = false }, n) end

function W.carry(d)
    local target = neighbour(d)
    if not target then
        if d < 0 or #windows_on(current()) <= 1 and current() == count then return end   -- alone at the end: already there
        target = count + 1
    end
    move_window({}, target)
end

function W.swap(d)
    local here, target = current(), neighbour(d)
    if not target then return end
    local mine, theirs = windows_on(here), windows_on(target)
    busy = true
    for _, w in ipairs(mine) do
        hl.dispatch(hl.dsp.window.move({ window = "address:" .. w.address, workspace = target, follow = false }))
    end
    for _, w in ipairs(theirs) do
        hl.dispatch(hl.dsp.window.move({ window = "address:" .. w.address, workspace = here, follow = false }))
    end
    busy = false
    focus(target)
end

-- insert an empty workspace before (-1) or after (+1) this one and go there;
-- the workspaces from that spot on shift up by one (several screens: a new one at the end)
function W.insert(d)
    if multi() then W.new() return end
    local here = current()
    if #windows_on(here) == 0 then return end          -- already on an empty workspace
    if full() then return end
    local target = d > 0 and here + 1 or here
    busy = true
    count = count + 1
    sync()
    for k = count - 1, target, -1 do move_all(k, k + 1) end
    busy = false
    focus(target)
end

function W.remove()
    local here = current()
    if count <= 1 then return end
    if multi() then                             -- its windows go to the neighbour on this screen
        local dest = neighbour(-1) or neighbour(1)
        if dest then move_all(here, dest); focus(dest) end
        return
    end
    busy = true
    local dest = here > 1 and here - 1 or 2
    move_all(here, dest)                       -- its windows go to the neighbour
    for k = here + 1, count do move_all(k, k - 1) end   -- close the gap
    count = count - 1
    sync()
    busy = false
    focus(math.max(1, math.min(here > 1 and here - 1 or 1, count)))
end

-- remove empty workspaces except the one you're on (the ones after them shift down)
function W.prune()
    if busy then return end
    local here = current()
    local removed, seen = false, shown()
    if multi() then                                  -- no renumbering across screens: only trim the end
        count = top_used()
        sync()
        return
    end
    busy = true
    for id = count, 1, -1 do
        if count <= 1 then break end
        if id ~= here and #windows_on(id) == 0 then
            for k = id + 1, count do move_all(k, k - 1) end
            count = count - 1
            if here > id then here = here - 1 end    -- the workspace you're on shifted down
            removed = true
        end
    end
    busy = false
    if removed then
        sync()
        focus(here)
    end
end

-- run it shortly after things change (Hyprland updates window counts after the event)
local pending = false
local function prune_soon()
    if pending then return end
    pending = true
    hl.timer(function() pending = false; W.prune() end, { timeout = 150, type = "oneshot" })
end

sync()
W.check()                                  -- include workspaces already in use
hl.on("window.open", function() W.check() end)
hl.on("window.move_to_workspace", function() W.check(); prune_soon() end)
hl.on("window.close", prune_soon)
hl.on("window.destroy", prune_soon)
hl.on("workspace.active", prune_soon)
-- a screen comes or goes: include what it shows; with one screen left the row closes up again
local function screens_changed()
    sync()                                       -- rules off before a new screen can attract anything
    hl.timer(function() W.check(); sync(); prune_soon() end, { timeout = 600, type = "oneshot" })
end
hl.on("monitor.added", screens_changed)
hl.on("monitor.removed", screens_changed)

return W
