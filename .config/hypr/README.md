# Hyprland — "Balcony" setup

Look based on [1amSimp1e/dots](https://github.com/1amSimp1e/dots) (balcony branch), rebuilt for
Hyprland 0.57. This is the only desktop now (GNOME was removed); the login screen is SDDM with a theme that matches the lock screen.

**Super** = the Windows key. One shortcut per action. Press **Super + I** any time to see this list on screen.

## Shortcuts

### Apps

| Keys | Action |
|---|---|
| `Super + Return` | Terminal (Alacritty + tmux) |
| `Alt + Return` | Floating terminal |
| `Super + Tab` | Window switcher: most recent first, previous window pre-selected (`Super + Tab` → `Enter` flips back) |
| `Super + Space` | **Spotlight** (results update as you type, in sections): **Top Hit** (a calculation like `100-36` or `5 km to mi`, else what you picked before for a similar search — it learns — else the best match) · **Applications** (also found by what they do, e.g. "browser") · **System** (lock, sleep, restart, shut down, log out, Wi-Fi, Bluetooth, Night Light, Do Not Disturb, Keep Awake, power mode, screenshot, empty trash, displays, notifications, clipboard, shortcuts) · **Documents · Folders · Images · Files** · **Search** the web / inside documents. **Quick Look** on the right: PDF first page, images, text, folder contents, details. **Enter** = open / go to the app / copy the result / run the action (restart, shut down, log out and empty trash ask for a second Enter) · **Shift + Enter** = app: new window · file: show in folder · **Ctrl + Enter** = search inside documents · **Esc** or Super + Space again closes |
| `Super + E` | Files (Nautilus) |
| `Ctrl + Alt + P` | Chrome — personal profile |
| `Ctrl + Alt + W` | Chrome — University profile |
| `Super + .` | Emoji picker (Smile) |
| `Super + V` | Clipboard history (`Enter` copy · `Alt + Delete` clear) |
| `Super + I` | This list of shortcuts (type to filter, `Esc` closes) |

### 1Password

| Keys | Action |
|---|---|
| `Ctrl + Shift + Space` | Quick Access |
| `Super + Shift + P` | Show / hide 1Password |
| `Super + Shift + L` | Lock 1Password |

### Windows

| Keys | Action |
|---|---|
| `Super + Q` | Close window |
| `Super + H / J / K / L` | Focus left / down / up / right |
| `Super + Shift + H / J / K / L` | Move window left / down / up / right |
| `Super + ← → ↑ ↓` | Resize window (hold to repeat) |
| `Super + T` | Toggle floating / tiled |
| `Super + F` | Maximize (keeps the bar) |
| `Super + Shift + F` | Real fullscreen |
| `Super + X` | Swap split direction (side-by-side ↔ stacked) |
| `Super + P` | Displays: Extend · Mirror · External only · Laptop only (also pops up when you plug in a monitor / projector) |
| `Super + left-drag` | Move window with the mouse |
| `Super + right-drag` | Resize window with the mouse |

### Workspaces

| Keys | Action |
|---|---|
| `Super + 1 … 9, 0` | Go to workspace 1 … 10 (past the last one: a new workspace at the end) |
| `Super + Shift + 1 … 9, 0` | Send window to exactly workspace 1 … 10 (stay here) |
| `Super + Ctrl + H / L` | Previous / next workspace (next at the end = add a new one) |
| `Super + Ctrl + Shift + H / L` | Take window to previous / next workspace |
| `Super + Alt + H / L` | Move the whole current workspace left / right (reorder workspaces) |
| `Super + Ctrl + Alt + H / L` | Insert a new empty workspace to the left / right of this one and go there (the ones after shift up) |
| `Super + Ctrl + Q` | Remove the current workspace (its windows move to the previous one; the rest shift down) |
| `Super + scroll` | Next / previous workspace (same rule) |
| 4-finger swipe ← → | Next / previous workspace (same rule) |

### Screenshots & tools

| Keys | Action |
|---|---|
| `Print` | Whole screen → saved to `~/Pictures/Screenshots` and copied |
| `Super + Shift + A` | Select an area → annotate / save in Swappy (`Esc` cancels) |
| `Super + Shift + C` | Colour picker (copies the hex code) |

### Session

| Keys | Action |
|---|---|
| `Super + Escape` | Lock screen |
| `Super + Shift + E` | Power menu (lock, suspend, log out, restart, shut down) |
| `Super + N` | Notification Center (open / close) |
| `Super + Shift + N` | Clear all notifications |

### Laptop keys

Volume, mute, mic mute, brightness and media (play/pause/next/previous) keys work as usual and
show a small pop-up. They also work on the lock screen.

## The bar (Waybar)


Icons: outline style — Octicons (`nf-oct-*`, in the Nerd Font) wherever one exists; coffee cup, battery, Wi-Fi, leaf and power from Lucide (`~/.local/share/fonts/Lucide`, official `lucide-static` font, ISC licence). App icons next to the workspace numbers are Lucide too (e.g. compass = Chrome, globe = Firefox, book with text = PDF viewer, notebook with pen = Obsidian; rules in `waybar/config.jsonc` → `window-rewrite`).

| Item | Click |
|---|---|
| Telescope | Spotlight (`Super + Space`) |
| 1 · 2 · 3 … | Workspaces, each with icons of the apps running on it — the current one is highlighted; click to switch, scroll to move |
| + | Add a new empty workspace at the end and go there |
| Bell | **Notification Center.** Click: open the panel on the right (notifications grouped by app, media player, Clear). Filled bell = notifications waiting (outline = nothing new). Right-click: **do not disturb** on / off (amber crossed-out bell); while on, notifications skip the pop-up and go silently to the panel, and they stay there when you turn it off. Volume / brightness pop-ups and critical alerts (low battery) still show. |
| Coffee cup | Caffeinate. **Click:** keep awake indefinitely (click again = off) · **Right-click:** choose time (30 min … 5 h, ∞, custom) and mode (screen + system / system only). Dim cup = off, amber cup + time left = on. |
| Moon | Night light. **Turns on at sunset and off at sunrise automatically** (Valparaíso times, recalculated daily). **Click:** on / off by hand (respected until the next sunset/sunrise) · **Scroll:** warmer / cooler while on (2500–6000 K). Hover shows today's times. |
| Power profile | **Click** to cycle: rocket = performance (gold) → meter = balanced → leaf = power saver (green). Hover shows the current one. Performance is limited when the laptop detects it's on your lap. |
| Wi-Fi | Network settings (`nmtui`) |
| Speaker | Sound settings · right-click mutes · scroll changes volume |
| Brightness | Scroll to change |
| Battery | Fills as it charges (empty · low · medium · full), bolt while charging, plug when plugged in but not charging · click to show % |
| Date | Today's date · hover for a calendar · click: Notification Center |
| Time | The time · click: Notification Center |
| Power | Power menu |

App indicators (1Password, Insync, ZapZap, Bluetooth, network…) are hidden behind the **‹** arrow on the right of the bar: click it to show or hide them.

## Automatic behaviour

- **Empty workspaces disappear:** as soon as you're not on an empty workspace it's removed and the ones after it shift down (like GNOME). The one you're on stays even when empty, so you can open something there.
- **Idle:** screen dims at 4.5 min, locks at 5 min, turns off at 5.5 min, suspends at 15 min
 . Videos and `caffeinate` prevent it.
- **Lid / suspend:** the screen is locked before sleeping.
- **Workspaces are a row** (like GNOME / macOS Spaces): workspaces 1 … N (up to 10) always exist, **empty ones stay** until you remove them (Super+Ctrl+Q), there are never gaps, and N is remembered across logins. Add one with **+** or by going past the end. Keys, Super+scroll, the 4-finger swipe and the bar all follow the same rule. Logic: `~/.config/hypr/workspaces.lua`.
- **Night light:** on at sunset, off at sunrise (timer `nightlight-auto.timer`, checks every 5 min). Location for the sun times: `LAT/LON` in `~/.config/hypr/scripts/suntimes`.
- **Battery:** power saver plan at 20 % (your previous plan comes back when you plug in, unless you changed it yourself), notification at 15 %, urgent one at 5 %, suspends at 3 % (`power-watch.timer`, every minute). On battery the blur is lighter (1 pass) to save power; on the charger it's back to 3.
- **App activation:** clicking a notification or link takes you to that app's window, switching workspace if needed.
- **Apps at login:** Everything in `~/.config/autostart` (1Password, Insync,
  ZapZap, Bluetooth, network applet).

## Terminal (colours follow the wallpaper)

tmux prefix is `Ctrl + Space` (or `Ctrl + B`).

| Keys | Action |
|---|---|
| `Alt + 1 … 9` | Go to tmux tab 1 … 9 |
| `prefix c` | New tab |
| `prefix \|` / `prefix -` | Split side by side / top–bottom |
| `prefix z` | Zoom pane (fullscreen pane) on/off |
| `prefix ,` | Rename tab |
| `prefix $` | Rename session |
| `prefix r` | Reload tmux config |

## Wallpaper & colours

Everything follows the wallpaper's colours: bar, window borders, launcher & menus,
notifications, lock screen, password dialog, PDF viewer and terminal.

| Command | What it does |
|---|---|
| `wallpaper ~/path/image.jpg` | Set the wallpaper and recolour the whole theme from it |
| `wallpaper ~/path/image.jpg --login` | Same, and also update the login screen — wallpaper and colours (asks for your password) |
| `wallpaper` | Show the current wallpaper |

How the colours are picked: the image's most vivid colour sets the **main hue** (dark tinted
bar, tinted light menus, terminal background); its **complementary colour** is the accent
(window border, "on" states of caffeinate / night light). Changing the wallpaper in any other
way is picked up at the next login. Generator: `~/.config/hypr/scripts/theme`.

## Backup (dotfiles)

Your config is versioned in Git (`~/.dotfiles`, files stay in place) and pushed to the private GitHub repo **gcarrenoc/hyprland-dotfiles**.

| Command | What it does |
|---|---|
| `dotfiles save "message"` | Save every change (and copies of the login-screen files) and push to GitHub |
| `dotfiles status` / `dotfiles diff` | What changed since the last save |
| `dotfiles log` | History |
| `dotfiles restore <file>` | Undo changes to a file |
| `dotfiles add <file>` | Start tracking a new file |

## Files

| What | Where |
|---|---|
| Hyprland (keys, look, rules) | `~/.config/hypr/hyprland.lua` — saved changes apply instantly; no-gap workspace logic in `~/.config/hypr/workspaces.lua` |
| Wallpaper & colours | `wallpaper <image>`; generated colour files: `waybar/colors.css`, `hypr/colors.lua`, `rofi/colors.rasi`, `swaync/colors.css`, `hypr/hyprlock-colors.conf`, `hypr/hyprtoolkit.conf` (password dialog), `zathura/colors` (PDF viewer), `alacritty/wallpaper-colors.toml`, `tmux/wallpaper.conf` |
| Lock screen / idle timings | `~/.config/hypr/hyprlock.conf`, `~/.config/hypr/hypridle.conf` |
| Screen scale | Laptop at **1.25** (fractional, 1536×960 logical): `hl.monitor` line in `hyprland.lua` and `LAPTOP` line in `scripts/display`. XWayland apps aren't upscaled (`force_zero_scaling`): rofi scales itself with `dpi: 120` in `rofi/config.rasi` (= 96 × scale; its sizes are in mm). Electron apps run on Wayland (`ELECTRON_OZONE_PLATFORM_HINT` in `uwsm/env-hyprland`). To change the scale, change those three numbers. |
| Helper scripts | `~/.config/hypr/scripts/` (spotlight, launcher (app library), windows, keybinds, display, power-watch, nightlight + suntimes, osd, screenshot, clipboard, powermenu) |
| Bar | `~/.config/waybar/config.jsonc`, `~/.config/waybar/style.css` |
| Launcher / power menu | `~/.config/rofi/` |
| Notifications | `~/.config/swaync/config.json` + `style.css` (swaync: pop-ups + Notification Center) |
| Terminal (Hyprland only) | `~/.config/alacritty/balcony.toml` (frosted window) + colours generated from the wallpaper by `~/.config/hypr/scripts/terminal-colors` (runs at login; run it by hand after changing the wallpaper) |
| Session environment | `~/.config/uwsm/env-hyprland` |
| Login screen (SDDM) | theme source `~/.config/hypr/sddm-theme/` (installed to `/usr/share/sddm/themes/hyprlock-match`), config `/etc/sddm.conf.d/10-hyprlock.conf` |

Check the Hyprland config for errors: `Hyprland --verify-config -c ~/.config/hypr/hyprland.lua`
