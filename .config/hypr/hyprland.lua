-- Hyprland — "Balcony" rice
-- Look based on github.com/1amSimp1e/dots (balcony branch), rewritten for
-- Hyprland 0.57 (Lua config). Started through uwsm ("Hyprland (uwsm-managed)"
-- in the login screen). GNOME stays available as the other session.
--
-- Palette (light mode; steel tones from the wallpaper):
--           surface #f2f5f7 / #ffffff  border #c5ced5  muted #7b8d96  steel #4f6672 / #8fa3b0
--           deep steel #3a4f5b  text #1c2228  alert #b24a4a

local HOME     = os.getenv("HOME")
local app      = "uwsm app -- "                      -- launch as a proper systemd unit
local terminal = app .. "alacritty --config-file " .. HOME .. "/.config/alacritty/balcony.toml"
local scripts  = HOME .. "/.config/hypr/scripts/"

-- colours generated from the wallpaper (scripts/theme); fallback if missing
local okc, C = pcall(dofile, HOME .. "/.config/hypr/colors.lua")
if not okc or type(C) ~= "table" then
    C = { active = { "rgba(f8ab59ff)", "rgba(ed7626ff)" }, inactive = "rgba(01185988)" }
end

--------------------
---- MONITORS ----
--------------------
hl.monitor({ output = "eDP-1", mode = "1920x1200@60", position = "0x0", scale = 1.25 })   -- fractional scaling: 1536x960 logical
hl.monitor({ output = "",      mode = "preferred",    position = "auto", scale = "auto" }) -- anything plugged in
-- XWayland apps are not upscaled (that blurs them): they draw at full resolution and scale
-- themselves — rofi menus via dpi in ~/.config/rofi/config.rasi (96 × scale).
hl.config({ xwayland = { force_zero_scaling = true } })

-------------------
---- AUTOSTART ----
-------------------
-- Apps from ~/.config/autostart (1Password, Insync, ZapZap,
-- Blueman, nm-applet) are started by uwsm automatically.
hl.on("hyprland.start", function()
    hl.exec_cmd(app .. "waybar")
    hl.exec_cmd(scripts .. "theme; " .. app .. "hyprpaper")   -- whole theme follows the wallpaper
    hl.exec_cmd(app .. "hypridle")
    hl.exec_cmd("systemctl --user start swaync")                      -- notifications + Notification Center
    hl.exec_cmd("sh -c '" .. app .. "hyprsunset -i & sleep 1; " .. scripts .. "nightlight restore; " .. scripts .. "nightlight auto'")   -- night light: last state, then follow the sun
    hl.exec_cmd("systemctl --user start hyprpolkitagent")             -- password prompts (pkexec, 1Password…)
    hl.exec_cmd("systemctl --user start localsearch-3.service")       -- file index for Super+Space (search inside documents)
    hl.exec_cmd(app .. "wl-paste --type text  --watch cliphist store")  -- clipboard history
    hl.exec_cmd(app .. "wl-paste --type image --watch cliphist store")
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

-- Frosted glass behind the bar (rofi menus are normal windows: window blur frosts them)
hl.layer_rule({ name = "blur-waybar",        match = { namespace = "^waybar$" },        blur = true, ignore_alpha = 0.2 })
-- Notifications (swaync) blur themselves: GTK asks for it via CSS backdrop-filter (layer rules are ignored for GTK 4.24 surfaces)


-- Plugging in a monitor / projector opens the display menu
hl.on("monitor.added", function() hl.exec_cmd(scripts .. "display --auto") end)

---------------
---- INPUT ----
---------------
hl.config({
    input = {
        kb_layout    = "latam",
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
hl.window_rule({ name = "spotlight", match = { class = "^(local\\.Spotlight)$" }, float = true, center = true, pin = true })   -- scripts/spotlight (GTK4)

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
hl.bind(M .. " + Space",              run(scripts .. "spotlight"))                  -- Spotlight: apps + files (↵ open / go to app, ⇧↵ new window / show in folder, ⌃↵ inside documents)
hl.bind(M .. " + E",                  run(app .. "nautilus --new-window"))
hl.bind("CTRL + ALT + P",             run(app .. "google-chrome-stable --profile-directory='Profile 1'"))  -- Chrome: personal
hl.bind("CTRL + ALT + W",             run(app .. "google-chrome-stable --profile-directory=Default"))    -- University
hl.bind(M .. " + period",             run(app .. "flatpak run it.mijorus.smile"))   -- emoji picker
hl.bind(M .. " + V",                  run(scripts .. "clipboard"))                  -- clipboard history
hl.bind(M .. " + I",                  run(scripts .. "keybinds"))                   -- list of all shortcuts

-- 1Password (same keys as GNOME)
hl.bind("CTRL + SHIFT + Space",       run("1password --quick-access"))
hl.bind(M .. " + SHIFT + P",          run("1password --toggle"))
hl.bind(M .. " + SHIFT + L",          run("1password --lock"))

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
hl.bind("Print",              run(scripts .. "screenshot full"))
hl.bind(M .. " + SHIFT + A",  run(scripts .. "screenshot area"))   -- area → annotate in swappy
hl.bind(M .. " + SHIFT + C",  run("hyprpicker -a"))

-- Session
hl.bind(M .. " + Escape",     run("loginctl lock-session"))
hl.bind(M .. " + SHIFT + E",  run(scripts .. "powermenu"))

-- Notifications
hl.bind(M .. " + N",          run("swaync-client -t -sw"))   -- Notification Center (open / close)
hl.bind(M .. " + SHIFT + N",  run("swaync-client -C -sw"))   -- clear all notifications

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
