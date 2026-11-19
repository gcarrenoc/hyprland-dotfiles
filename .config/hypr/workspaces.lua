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
--
-- Functions (global WS, so Waybar can call them via
-- `hyprctl dispatch 'function() WS.step(1) end'`):
--   WS.step(±1)   previous / next (next at the end = new)   Super+Ctrl+H/L, scroll, swipe
--   WS.go(n)      go to workspace n (past the end: a new one)  Super+1…0
--   WS.new()      add a workspace at the end and go there   + on the bar
--   WS.send(n)    send window to workspace n exactly         Super+Shift+1…0
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

local function sync()
    for i = 1, MAX do rules[i]:set_enabled(i <= count) end
    save()
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

-- grow the row to n (never past MAX); returns the usable position
local function ensure(n)
    n = math.max(1, math.min(n, MAX))
    if n > count then
        count = math.min(count + 1, MAX)   -- only ever add one at the end
        sync()
        n = math.min(n, count)
    end
    return n
end

-- safety: windows that end up beyond the row (apps, rules…) extend it
local busy = false
function W.check()
    if busy then return end
    local top = 0
    for _, ws in ipairs(hl.get_workspaces()) do
        if not ws.special and ws.id and ws.id > 0 and ws.windows > 0 and ws.id > top then top = ws.id end
    end
    if top > count then count = math.min(top, MAX); sync() end
end

-- grow the row up to n (creating the empty ones in between, so no gaps)
local function grow_to(n)
    n = math.max(1, math.min(n, MAX))
    if n > count then count = n; sync() end
    return n
end

function W.go(n)    focus(grow_to(n)) end          -- Super+N: exactly workspace N
local function last_and_empty()
    local here = current()
    return here == count and #windows_on(here) == 0
end

function W.new()
    if last_and_empty() then return end           -- already on an empty workspace at the end
    if count >= MAX then
        hl.exec_cmd("notify-send -a Workspaces -u low 'Maximum of 10 workspaces'")
        return
    end
    count = count + 1; sync(); focus(count)
end
function W.step(d)
    if d > 0 and last_and_empty() then return end  -- no second empty workspace
    local here = current(); focus(ensure(here + d))
end

function W.send(n)                              -- Super+Shift+N: exactly workspace N
    local target = grow_to(n)
    if target ~= current() then
        hl.dispatch(hl.dsp.window.move({ workspace = target, follow = false }))
    end
end

-- move a given window (by address) to workspace n exactly, without following it
function W.send_window(address, n)
    local target = grow_to(n)
    hl.dispatch(hl.dsp.window.move({ window = "address:" .. address, workspace = target, follow = false }))
end

function W.carry(d)
    local here = current()
    local target = ensure(here + d)
    if target ~= here then hl.dispatch(hl.dsp.window.move({ workspace = target })) end
end

function W.swap(d)
    local here = current()
    local target = here + d
    if target < 1 or target > count then return end
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
-- the workspaces from that spot on shift up by one
function W.insert(d)
    local here = current()
    if #windows_on(here) == 0 then return end          -- already on an empty workspace
    if count >= MAX then
        hl.exec_cmd("notify-send -a Workspaces -u low 'Maximum of 10 workspaces'")
        return
    end
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
    local removed = false
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

return W
