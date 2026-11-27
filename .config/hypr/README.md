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
| `Super + Space` | **Spotlight** (opens as a search bar; type and the rest unfolds, or press `↓` for apps and recent files; wildcards find files: `*.pdf`, `week_?.ipynb`, `*report*`, `calculus *.pdf`, `inf285/*.ipynb`; results update as you type, in sections): **Top Hit** (a calculation like `100-36` or `5 km to mi`, else what you picked before for a similar search — it learns — else the best match) · **Applications** (also found by what they do, e.g. "browser") · **System** (lock, sleep, restart, shut down, log out, Wi-Fi, Bluetooth, Night Light, Do Not Disturb, Keep Awake, power mode, screenshot, empty trash, displays, notifications, clipboard, shortcuts) · **Documents · Folders · Images · Files** · **Search** the web / inside documents. **Quick Look** on the right: PDF first page, images, text, folder contents, details. **Enter** = open / go to the app / copy the result / run the action (restart, shut down, log out and empty trash ask for a second Enter) · **Shift + Enter** = app: new window · file: show in folder · **Ctrl + Enter** = search inside documents · **Esc** or Super + Space again closes |
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
| `Super + Alt + P` | Lock 1Password |

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
| `Super + P` | Displays: Extend · Mirror · External only · Laptop only (also pops up when you plug in a monitor / projector; unplug the last one and the laptop's screen comes back) |
| `Super + left-drag` | Move window with the mouse |
| `Super + right-drag` | Resize window with the mouse |

### Workspaces

| Keys | Action |
|---|---|
| `Super + 1 … 9, 0` | Go to workspace 1 … 10 (past the last one: a new workspace at the end) |
| `Super + Shift + 1 … 9, 0` | Send window to workspace 1 … 10 (past the last one: one new workspace; stay here) |
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
| `Print` | **Screenshot tool** (like GNOME): the screen freezes; choose **Selection** (drag; move or resize it; remembered), **Screen** or **Window** (click one; saved with its rounded corners), **photo or video**, pointer on/off; the round button, Enter or Space captures, Esc closes. Keys inside: S · C · W · V (video) · P (pointer). No coloured window borders in the pictures. Recording: red dot on the bar, click it or press Print to stop (`~/Videos/Screencasts`) |
| `Shift + Print` | Whole screen at once (saved and copied) |
| `Alt + Print` | The active window at once, with its rounded corners |
| `Super + Shift + A` | Select an area → annotate / save in Swappy (`Esc` cancels) |
| `Super + Shift + C` | Colour picker (copies the hex code) |

### Session

| Keys | Action |
|---|---|
| `Super + Escape` | Lock screen |
| `Super + Shift + E` | Power menu (lock, suspend, hibernate, log out, restart, shut down) |
| `Super + N` | Notification Center (open / close) |
| `Super + Shift + N` | Clear all notifications |

### Panels

| Keys | Action |
|---|---|
| `Super + Ctrl + W` | Wi-Fi panel |
| `Super + Ctrl + B` | Bluetooth panel |
| `Super + Ctrl + S` | Sound panel |
| `Super + Ctrl + D` | Brightness and night light panel |
| `Super + Ctrl + P` | Battery, power mode and Caffeinate panel |

### Laptop keys

Volume, mute, mic mute, brightness and media (play/pause/next/previous) keys work as usual and
show a small pop-up. They also work on the lock screen.

### PDF viewer (Zathura)

Inside Zathura (`~/.config/zathura/zathurarc`).

| Keys | Action |
|---|---|
| `j` / `k` or `↓` / `↑` | Scroll down / up |
| `J` / `K` | Next / previous page |
| `Space` / `Shift + Space` | One screen down / up |
| `gg` / `G` | First / last page |
| `25G` | Go to page 25 (any number) |
| `Ctrl + o` / `Ctrl + i` | Jump back / forward (after a link or jump) |
| `+` / `-` or `Ctrl + scroll` | Zoom in / out |
| `=` | Actual size (100 %) |
| `s` / `a` | Fit width / fit whole page |
| `w` | Single page / continuous |
| `d` | Two pages side by side |
| `r` | Rotate |
| `Ctrl + r` | Dark reading mode (images keep their colours) |
| `F11` / `F5` | Fullscreen / presentation mode |
| `/` or `?` | Search forward / backward |
| `n` / `N` | Next / previous match |
| `Tab` | Table of contents (`Enter` opens a chapter) |
| `f` | Follow a link (type its number) |
| `m` + letter / `'` + letter | Set a mark / jump back to it |
| `Ctrl + c` | Copy the text selected with the mouse |
| `R` | Reload the file |
| `q` | Quit |

## The bar (Waybar)


Icons: [Font Awesome 7](https://fontawesome.com) (Arch package `otf-font-awesome`), also in the panels, menus, Spotlight and lock screen. Icon size = 94.7 % of the text size (17 px in 18 px text), so icons and digits share one centre. App icons next to the workspace numbers are the apps' own logos where a font has one (Font Awesome Brands, else the Nerd Font).

| Item | Click |
|---|---|
| Telescope | Spotlight (`Super + Space`) |
| 1 · 2 · 3 … | Workspaces, each with icons of the apps running on it — the current one is highlighted; click to switch, scroll to move |
| + | Add a new empty workspace at the end and go there |
| Amber icons | Shown only when something isn't as usual: crossed-out bell = do not disturb, cup = Caffeinate, leaf = power saver, rocket = performance. Click: Battery panel |
| Wi-Fi | **Wi-Fi panel:** on / off, networks (click to join; type the password if it is new), details, disconnect, forget, cable, VPN, network settings. Click again, click outside or Esc closes. Middle-click opens `nmtui` |
| Bluetooth | **Bluetooth panel:** on / off, your devices (click to connect; `…` to disconnect or forget; battery when known), nearby devices (click to pair, codes are shown there), blueman. Muted = off |
| Speaker | **Sound panel:** output and microphone (volume, mute, device), now playing, volume of each app. Click again, click outside or Esc closes · `m` mutes. Right-click mutes · scroll changes volume · middle-click opens the full mixer |
| Sun | **Brightness panel:** screen brightness and **night light** (on / off, warmth). Night light **turns on at sunset and off at sunrise automatically** (Valparaíso, or `latitude longitude` in `~/.config/hypr/location`; recalculated daily); what you choose by hand stays until the next one. Scroll changes the brightness |
| Battery | Always shows the percentage (the icon fills as it charges; bolt while charging, plug when plugged in but not charging). Click: **Battery panel** — time left, **power mode** (power saver · balanced · performance), **Caffeinate** (keep awake: until turned off, 30 min … 5 h), power in use, health and cycles, charge limit. Click again, click outside or Esc closes |
| Date | Today's date · hover for a calendar |
| Time | The time · click: **Notification Center** — **do not disturb** on top, then your notifications as cards, one per notification or one stack per app (click a stack to expand it; ✕ dismisses; `Super + Shift + N` clears all). While do not disturb is on, notifications skip the pop-up and go silently to the Center, and they stay there when you turn it off; volume / brightness pop-ups and critical alerts (low battery) still show |
| Power | Power menu |

App indicators (1Password, Insync, ZapZap…) are hidden behind the **‹** arrow on the right of the bar: click it to show or hide them.

## Automatic behaviour

- **Empty workspaces disappear:** as soon as you're not on an empty workspace it's removed and the ones after it shift down (like GNOME). The one you're on stays even when empty, so you can open something there.
- **Idle:** screen dims (to half of what it is, never brighter) at 4.5 min, locks at 5 min, turns off at 5.5 min, suspends at 15 min **on battery only**: on the charger it keeps working
 . Videos and `caffeinate` prevent it.
- **Lid / suspend:** the screen is locked before sleeping.
- **Workspaces are a row** (like GNOME / macOS Spaces): workspaces 1 … N (up to 10) always exist, **empty ones disappear** once you leave them, there are never gaps, and N is remembered across logins. Add one with **+** or by going past the end. Keys, Super+scroll, the 4-finger swipe and the bar all follow the same rule. Logic: `~/.config/hypr/workspaces.lua`. With several screens each workspace stays on its screen and nothing is renumbered.
- **Night light:** on at sunset, off at sunrise (timer `nightlight-auto.timer`, checks every 5 min). Location for the sun times: `LAT/LON` in `~/.config/hypr/scripts/suntimes`.
- **Battery:** power saver plan at 20 % (your previous plan comes back when you plug in, unless you changed it yourself), notification at 15 %, urgent one at 8 % (both also in do not disturb), hibernates at 5 % once you have tested it (`~/.config/hypr/scripts/hibernate --tested`), else suspends (`power-watch.timer`, every minute). On battery the blur is lighter (1 pass) to save power; on the charger it's back to 3.
- **App activation:** clicking a notification or link takes you to that app's window, switching workspace if needed.
- **If something crashes:** the bar, Spotlight, the panels, wallpaper, idle/lock and clipboard history are systemd user services and restart by themselves (`systemctl --user status waybar`).
- **Hibernation:** everything is saved to `/swapfile` on the encrypted disk (16 GB; zram is still used first) and the laptop turns off; on start, unlock the disk as usual and it all comes back. Power menu or Spotlight. The LTS boot entry never resumes: it is the fallback. Don't start Windows and change the shared boot partition with it hibernated if you can avoid it (it is unmounted first, just in case).
- **Firewall:** nothing from the network gets in unless this laptop started it (`/etc/nftables.conf`; mDNS allowed so printers and TVs are found; for a hotspot see the notes in the file).
- **App updates:** Claude Desktop and VS Code update by themselves; you're told only if that stops working (`~/.local/lib/apt_app.py`).
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

Your config is versioned in Git (`~/.dotfiles`, files stay in place) and pushed to the **public** GitHub repo **gcarrenoc/hyprland-dotfiles**. New machine: `~/.config/system-config/setup`.

| Command | What it does |
|---|---|
| `dotfiles save "message"` | Save every change (with copies of system files and the package lists), **scan for secrets** and push to the public GitHub repo; stops if something looks private |
| `dotfiles-scan --all` | Check every tracked file for secrets (your own private words: `~/.config/dotfiles-private`, never tracked) |
| `dotfiles status` / `dotfiles diff` | What changed since the last save |
| `dotfiles log` | History |
| `dotfiles restore <file>` | Undo changes to a file |
| `dotfiles add <file>` | Start tracking a new file |

**Sharing it:** someone else installs it with `~/.config/dotfiles/install` from a normal clone; they choose parts (core desktop, terminal, PDF, my apps…) and never get my personal files. The parts and their files are listed in `~/.config/dotfiles/components`: **when you add a new app or config, add it there too** so others can get it. Everything about my laptop or me (screen, keyboard, my own shortcuts) goes in `~/.config/hypr/local.lua`, not `hyprland.lua`.

## Files

`~/.config/hypr/local.lua`: this laptop and my own shortcuts (screen, keyboard layout, Chrome profiles, 1Password, emoji picker). `hyprland.lua` loads it; the installer for other people (`~/.config/dotfiles/install`) never copies it.

| What | Where |
|---|---|
| Hyprland (keys, look, rules) | `~/.config/hypr/hyprland.lua` — saved changes apply instantly; no-gap workspace logic in `~/.config/hypr/workspaces.lua` |
| Wallpaper & colours | `wallpaper <image>`; generated colour files: `waybar/colors.css`, `hypr/colors.lua`, `rofi/colors.rasi`, `swaync/colors.css`, `hypr/hyprlock-colors.conf`, `hypr/hyprtoolkit.conf` (password dialog), `zathura/colors` (PDF viewer), `alacritty/wallpaper-colors.toml`, `tmux/wallpaper.conf` |
| Lock screen / idle timings | `~/.config/hypr/hyprlock.conf`, `~/.config/hypr/hypridle.conf` |
| Screen scale | Laptop at **1.25** (fractional, 1536×960 logical): `LAPTOP` in `~/.config/hypr/local.lua` (`scripts/display` uses it too). XWayland apps aren't upscaled (that blurs them): rofi menus get the screen's dpi from `scripts/menu` |
| Boot menu | **rEFInd** (graphical: Arch · Windows 11 · reboot / shut down / firmware), [Brad's rEFInd theme](https://github.com/toptensoftware/brads-refind-theme) (copy in `~/.config/refind/themes/`). Menu: `~/.config/refind/refind.conf`; after editing either run `refind-theme` (installs to the EFI partition, asks for the password). Arch submenu (F2): LTS kernel, boot messages. Fallback: F12 → *Linux Boot Manager* (systemd-boot). |
| Helper scripts | `~/.config/hypr/scripts/` (spotlight, launcher (app library), windows, keybinds, display, power-watch, nightlight + suntimes, osd, screenshot, clipboard, powermenu) |
| Bar | `~/.config/waybar/config.jsonc`, `~/.config/waybar/style.css` |
| Launcher / power menu | `~/.config/rofi/` |
| Notifications | `~/.config/swaync/config.json` + `style.css` (swaync: pop-ups + Notification Center) |
| Terminal (Hyprland only) | `~/.config/alacritty/balcony.toml` (frosted window) + colours generated from the wallpaper by `~/.config/hypr/scripts/terminal-colors` (runs at login; run it by hand after changing the wallpaper) |
| Session environment | `~/.config/uwsm/env-hyprland` |
| Login screen (SDDM) | theme source `~/.config/hypr/sddm-theme/` (installed to `/usr/share/sddm/themes/hyprlock-match`), config `/etc/sddm.conf.d/10-hyprlock.conf` |

Check the Hyprland config for errors: `Hyprland --verify-config -c ~/.config/hypr/hyprland.lua`
