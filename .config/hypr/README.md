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
| `Super + D` | App launcher: **Enter** = go to the app if it's open (switches workspace), otherwise open it · **Shift + Enter** = new window here. Most-used apps first. |
| `Super + Tab` | Window switcher: most recent first, previous window pre-selected (`Super + Tab` → `Enter` flips back) |
| `Super + Space` | Search files (Spotlight-style): `Enter` open · `Shift + Enter` show in folder · `Ctrl + Enter` search inside documents |
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
| `Super + 1 … 9, 0` | Go to exactly workspace 1 … 10 (the empty ones in between are created) |
| `Super + Shift + 1 … 9, 0` | Send window to exactly workspace 1 … 10 (stay here) |
| `Super + Ctrl + H / L` | Previous / next workspace (next at the end = add a new one) |
| `Super + Ctrl + Shift + H / L` | Take window to previous / next workspace |
| `Super + Alt + H / L` | Move the whole current workspace left / right (reorder workspaces) |
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
| `Super + N` | Show last notification again |
| `Super + Shift + N` | Dismiss all notifications |

### Laptop keys

Volume, mute, mic mute, brightness and media (play/pause/next/previous) keys work as usual and
show a small pop-up. They also work on the lock screen.

## The bar (Waybar)

| Item | Click |
|---|---|
| Arch logo | App launcher (`Super + D`) |
| I · II · III … | Workspaces in use — the current one is highlighted; click to switch, scroll to move |
| + | Add a new empty workspace at the end and go there |
| ☕ Coffee cup | Caffeinate. **Click:** keep awake indefinitely (click again = off) · **Right-click:** choose time (30 min … 5 h, ∞, custom) and mode (screen + system / system only). Dim cup = off, amber cup + time left = on. |
| 🌙 Moon | Night light. **Turns on at sunset and off at sunrise automatically** (Valparaíso times, recalculated daily). **Click:** on / off by hand (respected until the next sunset/sunrise) · **Scroll:** warmer / cooler while on (2500–6000 K). Hover shows today's times. |
| Wi-Fi | Network settings (`nmtui`) |
| Speaker | Sound settings · right-click mutes · scroll changes volume |
| Brightness | Scroll to change |
| Battery | Click to show % |
| Clock | Click for the date · hover for a calendar |
| ⏻ | Power menu |

App indicators (1Password, Insync, TickTick, ZapZap, Bluetooth, network…) are hidden behind the **‹** arrow on the right of the bar: click it to show or hide them.

## Automatic behaviour

- **Idle:** screen dims at 4.5 min, locks at 5 min, turns off at 5.5 min, suspends at 15 min
 . Videos and `caffeinate` prevent it.
- **Lid / suspend:** the screen is locked before sleeping.
- **Workspaces are a row** (like GNOME / macOS Spaces): workspaces I … N (up to X) always exist, **empty ones stay** until you remove them (Super+Ctrl+Q), there are never gaps, and N is remembered across logins. Add one with **+** or by going past the end. Keys, Super+scroll, the 4-finger swipe and the bar all follow the same rule. Logic: `~/.config/hypr/workspaces.lua`.
- **Night light:** on at sunset, off at sunrise (timer `nightlight-auto.timer`, checks every 5 min). Location for the sun times: `LAT/LON` in `~/.config/hypr/scripts/suntimes`.
- **Battery:** notification at 15 %, urgent one at 5 %, suspends at 3 % (`power-watch.timer`, every minute). On battery the blur is lighter (1 pass) to save power; on the charger it's back to 3.
- **App activation:** clicking a notification or link takes you to that app's window, switching workspace if needed.
- **Apps at login:** at login **TickTick opens on workspace X** (only its first window; later windows open where you are). Everything in `~/.config/autostart` (1Password, Insync, TickTick, Betterbird,
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
notifications, lock screen and terminal.

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
| Wallpaper & colours | `wallpaper <image>`; generated colour files: `waybar/colors.css`, `hypr/colors.lua`, `rofi/colors.rasi`, `dunst/dunstrc.d/90-colors.conf`, `hypr/hyprlock-colors.conf`, `alacritty/wallpaper-colors.toml`, `tmux/wallpaper.conf` |
| Lock screen / idle timings | `~/.config/hypr/hyprlock.conf`, `~/.config/hypr/hypridle.conf` |
| Helper scripts | `~/.config/hypr/scripts/` (launcher, spotlight, windows, keybinds, display, power-watch, nightlight + suntimes, osd, screenshot, clipboard, powermenu) |
| Bar | `~/.config/waybar/config.jsonc`, `~/.config/waybar/style.css` |
| Launcher / power menu | `~/.config/rofi/` |
| Notifications | `~/.config/dunst/dunstrc` |
| Terminal (Hyprland only) | `~/.config/alacritty/balcony.toml` (frosted window) + colours generated from the wallpaper by `~/.config/hypr/scripts/terminal-colors` (runs at login; run it by hand after changing the wallpaper) |
| Session environment | `~/.config/uwsm/env-hyprland` |
| Login screen (SDDM) | theme source `~/.config/hypr/sddm-theme/` (installed to `/usr/share/sddm/themes/hyprlock-match`), config `/etc/sddm.conf.d/10-hyprlock.conf` |

Check the Hyprland config for errors: `Hyprland --verify-config -c ~/.config/hypr/hyprland.lua`
