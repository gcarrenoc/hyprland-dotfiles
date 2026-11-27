-- local.lua — this laptop and this person only. Loaded by hyprland.lua; NOT copied by the installer
-- (~/.config/dotfiles/install makes a template instead). Plain Lua with the hl.* API.

-- the built-in screen: fractional scaling 1.25 → 1536x960 logical
LAPTOP = { output = "eDP-1", mode = "1920x1200@60", position = "0x0", scale = 1.25 }
KB_LAYOUT = "latam"

local app = "uwsm app -- "
local function run(cmd) return hl.dsp.exec_cmd(cmd) end
local M = "SUPER"

hl.bind("CTRL + ALT + P",             run(app .. "google-chrome-stable --profile-directory='Profile 1'"))  -- Chrome: personal
hl.bind("CTRL + ALT + W",             run(app .. "google-chrome-stable --profile-directory=Default"))    -- University
hl.bind(M .. " + period",             run(app .. "flatpak run it.mijorus.smile"))   -- emoji picker

-- 1Password
hl.bind("CTRL + SHIFT + Space",       run("1password --quick-access"))
hl.bind(M .. " + SHIFT + P",          run("1password --toggle"))
hl.bind(M .. " + ALT + P",            run("1password --lock"))            -- (Super+Shift+L moves a window right)
