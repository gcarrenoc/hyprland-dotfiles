# hyprland-dotfiles

My Arch Linux desktop: **Hyprland 0.57** (Lua config) on a ThinkPad X13 Gen 3, with fractional scaling at 1.25.
The look started from [1amSimp1e/dots](https://github.com/1amSimp1e/dots) (balcony branch) and was rebuilt for Hyprland 0.57.
Everything recolours itself from the wallpaper.

> **Full guide and every shortcut:** [`.config/hypr/README.md`](../.config/hypr/README.md) ([PDF](../.config/hypr/README.pdf)).
> On the desktop, **Super + I** shows the same list, searchable.

## What's inside

| Part | Tool | Config |
|---|---|---|
| Compositor | Hyprland 0.57 (Lua), started with uwsm | [`.config/hypr/hyprland.lua`](../.config/hypr/hyprland.lua), [`workspaces.lua`](../.config/hypr/workspaces.lua) |
| Bar | Waybar, frosted, one 18 px size for text and icons ([Octicons](https://primer.style/octicons) + [Lucide](https://lucide.dev)) | [`.config/waybar/`](../.config/waybar) |
| Bar panels | Frosted GTK4 panels that drop down from the bar: **Wi-Fi, Bluetooth, sound, brightness + night light, battery + power mode**. One resident program, opens in about 0.1 s | [`bar-panels`](../.config/hypr/scripts/bar-panels), [`panels/`](../.config/hypr/scripts/panels) |
| Notifications | swaync: floating cards, Do Not Disturb that keeps muted notifications | [`.config/swaync/`](../.config/swaync) |
| Launcher | **Spotlight** (Super + Space): resident GTK4 app with apps, files, live calculator, web search, system actions and Quick Look | [`.config/hypr/scripts/spotlight`](../.config/hypr/scripts/spotlight) |
| Menus | Rofi, frosted (power menu, clipboard, windows) | [`.config/rofi/`](../.config/rofi) |
| Lock / idle | hyprlock + hypridle (locks before sleep without flashing the apps) | [`hyprlock.conf`](../.config/hypr/hyprlock.conf), [`hypridle.conf`](../.config/hypr/hypridle.conf) |
| Login | SDDM with a theme that matches the lock screen | [`.config/hypr/sddm-theme/`](../.config/hypr/sddm-theme) |
| Boot menu | rEFInd with [Brad's theme](https://github.com/toptensoftware/brads-refind-theme) (Arch + Windows 11) | [`.config/refind/`](../.config/refind) |
| Terminal | Alacritty + tmux, colours from the wallpaper | [`.config/alacritty/`](../.config/alacritty), [`.config/tmux/`](../.config/tmux) |
| Shell | Fish inside tmux; Bash stays the login shell and runs the scripts | [`.config/fish/`](../.config/fish), [`.bashrc`](../.bashrc) |
| PDF / books | Zathura (dark reading mode, Ctrl+C copies) | [`.config/zathura/`](../.config/zathura) |

## Small tools

| Command | What it does |
|---|---|
| `wallpaper <image>` | Sets the wallpaper and recolours the bar, borders, menus, terminal, lock screen and login screen from it |
| `caffeinate [2h \| inf \| -s …]` | Keeps the laptop awake, macOS-style. It also lives in the tray. |
| `status-tray` | Tray icon for caffeinate, with a menu |
| `nightlight` | hyprsunset night light that turns on at sunset and off at sunrise (local sun times). Controlled from the brightness panel. |
| `claude-desktop-update` | Installs and updates [Claude Desktop](https://claude.ai/download) in `~/.local/opt` from Anthropic's signed apt repo. It verifies the key fingerprint, signature and checksums, needs no root, and runs silently. |
| `vscode-update` | The same for [VS Code](https://code.visualstudio.com), from Microsoft's signed repo |
| `google-tasks` | Google Tasks in its own Chrome window; goes to it if it's already open |
| `cnew` / `cpick` / `cpurge` | Start, resume and delete Claude Code conversations (Fish and Bash) |
| `jupyter-app` / `jupyter-tray` | JupyterLab as a desktop app with a tray icon to stop it |
| `refind-theme` | Installs the rEFInd menu and theme to the EFI partition |
| `dotfiles` | Manages this repo (see below) |

Background jobs run as systemd user units in [`.config/systemd/user/`](../.config/systemd/user): night light, low-battery power saver, Claude Desktop and VS Code updates, the tray and JupyterLab.

## How the repo works

It's a **bare git repo**: the files stay where they live in `$HOME`, and git's data lives in `~/.dotfiles`.
[`dotfiles`](../.local/bin/dotfiles) is a small wrapper around git:

```bash
dotfiles status            # any git command works
dotfiles add ~/.config/foo # start tracking a file
dotfiles save "message"    # copy the tracked /etc files, commit everything, push
```

A few system files (SDDM, keyboard layout, reflector, zram) are copied into
[`.config/system-config/etc/`](../.config/system-config/etc) on each save, so they're versioned too.

### Using it on another machine

These are personal configs for one laptop, so read before you copy. To try them:

```bash
git clone --bare https://github.com/gcarrenoc/hyprland-dotfiles.git ~/.dotfiles
alias dotfiles='git --git-dir=$HOME/.dotfiles --work-tree=$HOME'
dotfiles checkout          # stops if it would overwrite your files: move those away first
dotfiles config status.showUntrackedFiles no
```

Hyprland ≥ 0.57 with Lua config is required. The scripts expect Arch packages such as
`waybar rofi swaync hyprlock hypridle hyprpaper hyprsunset uwsm alacritty tmux zathura-pdf-mupdf libqalculate python-gobject libayatana-appindicator gtk4-layer-shell libpulse playerctl networkmanager blueman power-profiles-daemon upower brightnessctl fish fzf zoxide`
and a Nerd Font (PaperMono Nerd Font).

## Credits and licences

My own work here is under the [MIT licence](LICENSE). It doesn't cover the third-party parts below:

- Look based on [1amSimp1e/dots](https://github.com/1amSimp1e/dots) (GPL-3.0). The [Waybar](../.config/waybar) and [Rofi](../.config/rofi) files started from it and from [adi1090x/rofi](https://github.com/adi1090x/rofi) (GPL-3.0), so they are not under MIT.
- Current wallpaper: photo by Arnaud Mariat on [Unsplash](https://unsplash.com/photos/45Z6hW1dQMI). The repo only holds a link to the local file, not the photo.
- [Lucide](https://lucide.dev) icon font: ISC, see [`LICENSE`](../.local/share/fonts/Lucide/LICENSE).
- [Brad's rEFInd theme](https://github.com/toptensoftware/brads-refind-theme) by Topten Software: Apache 2.0, see its [`readme.md`](../.config/refind/themes/brads-refind-theme/readme.md).
- Third-party apps and fonts belong to their authors.
