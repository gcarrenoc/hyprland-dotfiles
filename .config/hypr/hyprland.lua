-- Hyprland — "Balcony" rice
-- Look based on github.com/1amSimp1e/dots (balcony branch), rewritten for
-- Hyprland 0.57 (Lua config). Started through uwsm ("Hyprland (uwsm-managed)"
-- in the login screen). Colours come from the wallpaper (scripts/theme → colors.lua).

local HOME     = os.getenv("HOME")
local app      = "uwsm app -- "                      -- launch as a proper systemd unit
local terminal = app .. "alacritty --config-file " .. HOME .. "/.config/alacritty/balcony.toml"
local scripts  = HOME .. "/.config/hypr/scripts/"

-- colours generated from the wallpaper (scripts/theme); fallback if missing
-- What belongs to this person / laptop (screen, keyboard, own shortcuts) is in local.lua, which the
-- installer never copies (it makes a template). It may set LAPTOP and KB_LAYOUT and add its own binds.
LAPTOP, KB_LAYOUT = { output = "eDP-1", mode = "preferred", position = "0x0", scale = "auto" }, "us"
local okl, err = pcall(dofile, HOME .. "/.config/hypr/local.lua")
if not okl and not tostring(err):find("No such file") then hl.notification({ text = "local.lua: " .. tostring(err), timeout = 10000 }) end

local okc, C = pcall(dofile, HOME .. "/.config/hypr/colors.lua")
if not okc or type(C) ~= "table" then
    C = { active = { "rgba(f8ab59ff)", "rgba(ed7626ff)" }, inactive = "rgba(01185988)" }
end

--------------------
---- MONITORS ----
--------------------
hl.monitor(LAPTOP)                                                                    -- the built-in screen (local.lua)
hl.monitor({ output = "",      mode = "preferred",    position = "auto", scale = "auto" }) -- anything plugged in
-- XWayland apps are not upscaled (that blurs them): they draw at full resolution and scale
-- themselves — rofi menus via dpi in ~/.config/rofi/config.rasi (96 × scale).
hl.config({ xwayland = { force_zero_scaling = true } })

-------------------
---- AUTOSTART ----
-------------------
-- Apps in ~/.config/autostart (and /etc/xdg/autostart: Blueman, nm-applet) are started by uwsm automatically.
-- The bar, Spotlight, the panels, wallpaper, idle/lock, night light and clipboard history are systemd
-- user services (enabled for graphical-session.target): they start with the session and come back
-- if they crash.  systemctl --user status waybar   ·   journalctl --user -u bar-panels
local services = "waybar spotlight bar-panels hyprpaper hypridle hyprsunset clipboard-history@text clipboard-history@image"
hl.on("hyprland.start", function()
    hl.exec_cmd(scripts .. "theme")                                   -- whole theme follows the wallpaper
    hl.exec_cmd("systemctl --user start swaync")                      -- notifications + Notification Center
    hl.exec_cmd("systemctl --user start hyprpolkitagent")             -- password prompts (pkexec, 1Password…)
    hl.exec_cmd("systemctl --user start localsearch-3.service")       -- file index for Super+Space (search inside documents)
    hl.exec_cmd("sh -c 'sleep 5; systemctl --user start " .. services .. "'")   -- safety net: no-op if they already run
    hl.exec_cmd("hyprctl setcursor Adwaita 24")
end)

-----------------------
---- LOOK AND FEEL ----
-----------------------
hl.config({
    general = {
        gaps_in     = 3,
        gaps_out    = { top = 3, right = 5, bottom = 5, left = 5 },   -- small gap under the bar
        border_size = 3,
        col = {
            active_border   = { colors = C.active, angle = 45 },   -- complement of the wallpaper hue
            inactive_border = C.inactive,
        },
        resize_on_border = true,
        layout = "dwindle",
    },

    decoration = {
        rounding       = 19,
        rounding_power = 6,   -- 2 = circular corners, 4+ = squircle (iOS/macOS-style)
        blur = {
            enabled = true,
            size    = 10,
            passes  = 3,
            vibrancy = 0.17,
        },
        -- no coloured glow: a plain soft shadow; the focused window is marked by its border
        shadow = {
            enabled        = true,
            range          = 10,
            render_power   = 3,
            color          = "rgba(00000045)",
            color_inactive = "rgba(00000035)",
        },
    },

    animations = { enabled = true },

    dwindle = { preserve_split = true },

    misc = {
        force_default_wallpaper  = 0,
        disable_hyprland_logo    = true,
        disable_splash_rendering = true,
        mouse_move_enables_dpms  = true,
        key_press_enables_dpms   = true,
        focus_on_activate        = true,   -- notifications/links take you to their app (switches workspace)
        allow_session_lock_restore = true, -- if the lock screen crashes, a new one can take over
        bell_sound               = "none", -- no system bell sound (rofi, terminal…); "default" brings it back
    },
})

-- Calm animations (Balcony's bouncy "overshot" curve removed on request)
hl.curve("smooth",   { type = "bezier", points = { {0.25, 1},    {0.5, 1}    } })
hl.animation({ leaf = "windows",    enabled = true, speed = 2.5, bezier = "smooth",   style = "popin 95%" })  -- calm open: slight fade-zoom
hl.animation({ leaf = "windowsOut", enabled = true, speed = 2,   bezier = "smooth",   style = "popin 95%" })  -- calm close
hl.animation({ leaf = "windowsMove", enabled = false })  -- instant maximize/fullscreen/move/resize (no bounce)
hl.animation({ leaf = "fade",       enabled = true, speed = 5,   bezier = "default" })
hl.animation({ leaf = "layers",     enabled = true, speed = 3,   bezier = "smooth",   style = "fade" })
hl.animation({ leaf = "workspaces", enabled = false })   -- instant workspace switch (no bouncy slide)
hl.animation({ leaf = "border",     enabled = true, speed = 10,  bezier = "default" })

-- Screenshots without the coloured borders: scripts/screenshot and the Print tool hide them (transparent,
-- so nothing moves) for the instant a frame is taken:  hyprctl dispatch 'function() Borders(false) end'
function Borders(show)
    hl.animation({ leaf = "border", enabled = false })      -- switch at once, no fade
    if show then
        hl.config({ general = { col = { active_border = { colors = C.active, angle = 45 }, inactive_border = C.inactive } } })
        hl.timer(function() hl.animation({ leaf = "border", enabled = true, speed = 10, bezier = "default" }) end,
                 { timeout = 100, type = "oneshot" })
    else
        hl.config({ general = { col = { active_border = "rgba(00000000)", inactive_border = "rgba(00000000)" } } })
    end
end

-- Frosted glass behind the bar (rofi menus are normal windows: window blur frosts them)
hl.layer_rule({ name = "blur-waybar",        match = { namespace = "^waybar$" },        blur = true, ignore_alpha = 0.2 })
-- Notifications (swaync) blur themselves: GTK asks for it via CSS backdrop-filter (layer rules are ignored for GTK 4.24 surfaces)


-- Never left without a screen: "External only" turns the laptop's screen off, so when the last
-- monitor is unplugged it comes back on
hl.on("monitor.removed", function()
    hl.timer(function()
        for _, m in ipairs(hl.get_monitors() or {}) do
            if m.name ~= "FALLBACK" then return end
        end
        hl.monitor({ output = LAPTOP.output, mode = LAPTOP.mode, position = LAPTOP.position, scale = LAPTOP.scale, mirror = "", disabled = false })   -- LAPTOP: local.lua
    end, { timeout = 500, type = "oneshot" })
end)

-- Plugging in a monitor / projector opens the display menu
hl.on("monitor.added", function() hl.exec_cmd(scripts .. "display --auto") end)

---------------
---- INPUT ----
---------------
hl.config({
    input = {
        kb_layout    = KB_LAYOUT,   -- local.lua
        follow_mouse = 1,
        sensitivity  = 0,
        touchpad = {
            natural_scroll = true,
            tap_to_click   = true,
        },
    },
})

-- 4-finger swipe left/right = next/previous workspace (same rule as the keys: see workspaces.lua)
hl.gesture({ fingers = 4, direction = "left",  action = function() WS.step(1) end })
hl.gesture({ fingers = 4, direction = "right", action = function() WS.step(-1) end })

--------------------------
---- WINDOW RULES ----
--------------------------
hl.window_rule({ name = "suppress-maximize", match = { class = ".*" }, suppress_event = "maximize" })

-- Floating utility windows
for _, cls in ipairs({
    "^(org.pulseaudio.pavucontrol)$", "^(blueman-manager)$", "^(nm-connection-editor)$",
    "^(xdg-desktop-portal-gtk)$", "^(hyprland-run)$", "^(it.mijorus.smile)$",
    "^(org.gnome.Calculator)$", "^(swappy)$",
}) do
    hl.window_rule({ name = "float " .. cls, match = { class = cls }, float = true })
end
hl.window_rule({ name = "pavucontrol-size", match = { class = "^(org.pulseaudio.pavucontrol)$" }, size = "800 500", center = true })
hl.window_rule({ name = "file-dialogs",      match = { title = "^(Open File|Save File|Open Folder|Save As|Choose Files?)(.*)$" }, float = true, center = true })
hl.window_rule({ name = "pip",               match = { title = "^(Picture.in.[Pp]icture)$" }, float = true, pin = true })

-- rofi menus run as normal windows (normal-window in rofi config) so they get
-- the same squircle corners, blur and border as apps: float, centered, focused
hl.window_rule({ name = "rofi-menus", match = { class = "^(rofi|Rofi)$" }, float = true, center = true, stay_focused = true, pin = true })

-- Floating "fly" terminal (Alt+Return)
hl.window_rule({ name = "fly-term", match = { class = "^(fly-term)$" }, float = true, size = "900 550", center = true })

-- Only the terminal is see-through (via its own config: ~/.config/alacritty/balcony.toml)

-- XWayland drag fix (from the Hyprland example)
hl.window_rule({
    name  = "fix-xwayland-drags",
    match = { class = "^$", title = "^$", xwayland = true, float = true, fullscreen = false, pin = false },
    no_focus = true,
})

---------------------
---- KEYBINDINGS ----
---------------------
local M = "SUPER"
local function run(cmd) return hl.dsp.exec_cmd(cmd) end

-- Apps
hl.bind(M .. " + Return",             run(terminal))
hl.bind("ALT + Return",               run(terminal .. " --class fly-term"))          -- floating terminal
hl.bind(M .. " + Tab",                run(scripts .. "windows"))                    -- window switcher (recent first)
hl.bind(M .. " + Space",              run(scripts .. "spotlight-toggle"))                  -- Spotlight: apps + files (↵ open / go to app, ⇧↵ new window / show in folder, ⌃↵ inside documents)
hl.bind(M .. " + E",                  run(app .. "nautilus --new-window"))
hl.bind(M .. " + V",                  run(scripts .. "clipboard"))                  -- clipboard history
hl.bind(M .. " + I",                  run(scripts .. "keybinds"))                   -- list of all shortcuts

-- Windows
hl.bind(M .. " + Q",                  hl.dsp.window.close())
hl.bind(M .. " + T",                  hl.dsp.window.float({ action = "toggle" }))
hl.bind(M .. " + F",                  hl.dsp.window.fullscreen({ mode = "maximized" }))
hl.bind(M .. " + SHIFT + F",          hl.dsp.window.fullscreen({ mode = "fullscreen" }))
hl.bind(M .. " + P",                  run(scripts .. "display"))                    -- displays: extend / mirror / external / laptop
hl.bind(M .. " + X",                  hl.dsp.layout("togglesplit"))

for key, dir in pairs({ h = "left", j = "down", k = "up", l = "right" }) do
    hl.bind(M .. " + " .. key,           hl.dsp.focus({ direction = dir }))
    hl.bind(M .. " + SHIFT + " .. key,   hl.dsp.window.move({ direction = dir }))
end
hl.bind(M .. " + left",  hl.dsp.window.resize({ x = -40, y = 0,   relative = true }), { repeating = true })
hl.bind(M .. " + right", hl.dsp.window.resize({ x = 40,  y = 0,   relative = true }), { repeating = true })
hl.bind(M .. " + up",    hl.dsp.window.resize({ x = 0,   y = -40, relative = true }), { repeating = true })
hl.bind(M .. " + down",  hl.dsp.window.resize({ x = 0,   y = 40,  relative = true }), { repeating = true })

hl.bind(M .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind(M .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Workspaces
-- No gaps: workspace N only exists if 1…N-1 do (see workspaces.lua)
WS = dofile(HOME .. "/.config/hypr/workspaces.lua")   -- global, so Waybar can call WS.step() via hyprctl

-- Drag a file (text, image…) to the left / right screen edge and hold: the previous / next workspace
-- comes up, like macOS. While the left button is down, invisible edge strips listen for drag-and-drop
-- only (scripts/panels/drag_edges.py in bar-panels). The click itself always goes through untouched.
-- Also over the bar: hover a workspace button with it and that workspace comes up.
-- A click that starts on the bar itself shows nothing, so the bar's own clicks are never in the way.
-- Each click gets an id: press and release are sent as two separate messages, and a quick touchpad
-- tap can deliver them out of order, so the panels app ignores a press whose release it already saw.
local dragging, click = false, math.random(1, 1000000)
local function drag_edges(action)
    hl.exec_cmd("gdbus call --session --dest local.BarPanels --object-path /local/BarPanels "
        .. "--method org.freedesktop.Application.ActivateAction " .. action .. " '[<int32 " .. click .. ">]' '{}'")
end
local function on_bar()
    local p, m = hl.get_cursor_pos(), hl.get_monitor_at_cursor()
    local top = m and type(m.reserved) == "table" and m.reserved.top or 0
    return p and m and p.y - m.position.y < top
end
hl.bind("mouse:272", function()
    if on_bar() then return end
    dragging, click = true, click % 2000000000 + 1
    drag_edges("drag-start")
end, { ignore_mods = true, non_consuming = true, transparent = true })
hl.bind("mouse:272", function()
    if not dragging then return end
    dragging = false
    drag_edges("drag-end")
end, { release = true, ignore_mods = true, non_consuming = true, transparent = true })

for i = 1, 10 do
    local key = i % 10
    hl.bind(M .. " + " .. key,         function() WS.go(i) end)
    hl.bind(M .. " + SHIFT + " .. key, function() WS.send(i) end)
end
hl.bind(M .. " + mouse_down", function() WS.step(1) end)
hl.bind(M .. " + mouse_up",   function() WS.step(-1) end)
hl.bind(M .. " + CTRL + H",          function() WS.step(-1) end)                         -- previous workspace
hl.bind(M .. " + CTRL + L",          function() WS.step(1) end)                          -- next workspace (at most one past the last used)
hl.bind(M .. " + CTRL + SHIFT + H",  function() WS.carry(-1) end)                        -- take window to previous workspace
hl.bind(M .. " + CTRL + SHIFT + L",  function() WS.carry(1) end)                         -- take window to next workspace
hl.bind(M .. " + ALT + H",           function() WS.swap(-1) end)                         -- move this workspace left (reorder)
hl.bind(M .. " + ALT + L",           function() WS.swap(1) end)                          -- move this workspace right (reorder)
hl.bind(M .. " + CTRL + ALT + H",    function() WS.insert(-1) end)                       -- new empty workspace to the left
hl.bind(M .. " + CTRL + ALT + L",    function() WS.insert(1) end)                        -- new empty workspace to the right
hl.bind(M .. " + CTRL + Q",           function() WS.remove() end)                         -- remove this workspace (windows → previous)

-- Screenshots, colour picker
hl.bind("Print",              run(scripts .. "panel screenshot"))   -- GNOME-style: selection / screen / window, photo or video
hl.bind("SHIFT + Print",      run(scripts .. "screenshot full"))    -- whole screen at once
hl.bind("ALT + Print",        run(scripts .. "screenshot window"))  -- the active window at once
hl.bind(M .. " + SHIFT + A",  run(scripts .. "screenshot area"))   -- area → annotate in swappy
hl.bind(M .. " + SHIFT + C",  run("hyprpicker -a"))

-- Session
hl.bind(M .. " + Escape",     run("loginctl lock-session"))
hl.bind(M .. " + SHIFT + E",  run(scripts .. "powermenu"))

-- Notifications
hl.bind(M .. " + N",          run("swaync-client -t -sw"))   -- Notification Center (open / close)
hl.bind(M .. " + SHIFT + N",  run("swaync-client -C -sw"))   -- clear all notifications

-- Panels of the bar (Esc closes)
hl.bind(M .. " + CTRL + W",   run(scripts .. "panel wifi"))         -- Wi-Fi
hl.bind(M .. " + CTRL + B",   run(scripts .. "panel bluetooth"))    -- Bluetooth
hl.bind(M .. " + CTRL + S",   run(scripts .. "panel sound"))        -- sound
hl.bind(M .. " + CTRL + D",   run(scripts .. "panel brightness"))   -- brightness and night light
hl.bind(M .. " + CTRL + P",   run(scripts .. "panel battery"))      -- battery and power mode

-- Media / brightness keys (with on-screen notification)
hl.bind("XF86AudioRaiseVolume",  run(scripts .. "osd volume up"),     { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume",  run(scripts .. "osd volume down"),   { locked = true, repeating = true })
hl.bind("XF86AudioMute",         run(scripts .. "osd volume mute"),   { locked = true })
hl.bind("XF86AudioMicMute",      run(scripts .. "osd mic mute"),      { locked = true })
hl.bind("XF86MonBrightnessUp",   run(scripts .. "osd brightness up"),   { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", run(scripts .. "osd brightness down"), { locked = true, repeating = true })
hl.bind("XF86AudioNext",  run("playerctl next"),       { locked = true })
hl.bind("XF86AudioPause", run("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  run("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev",  run("playerctl previous"),   { locked = true })
