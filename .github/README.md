# hyprland-dotfiles

An Arch Linux desktop on **Hyprland 0.57** (Lua config): a frosted bar with drop-down panels, a
Spotlight launcher, a GNOME-style screenshot tool, and colours that follow the wallpaper.
Made on a ThinkPad X13 Gen 3; the look started from [1amSimp1e/dots](https://github.com/1amSimp1e/dots) (balcony branch).

**Take only what you want:** the installer asks for each part, so you can have the desktop without
my apps. Nothing personal to me (shell config, default apps, boot menu, screen and keyboard) is
copied.

## Install

Needs Arch Linux with Hyprland ≥ 0.57 and uwsm.

```bash
git clone https://github.com/gcarrenoc/hyprland-dotfiles.git ~/hyprland-dotfiles
~/hyprland-dotfiles/.config/dotfiles/install            # asks for each part below
```

| Part | What you get |
|---|---|
| **core** (always) | Hyprland config, Waybar, the panels (Wi-Fi, Bluetooth, sound, brightness + night light, battery + power mode + keep awake), Spotlight (Super + Space), notifications with do not disturb, lock and idle, the screenshot tool (Print), the wallpaper theme, the shortcut list (Super + I) |
| terminal | Alacritty + tmux + Fish, colours from the wallpaper |
| pdf | Zathura with the theme's colours |
| claude-code | `cnew` / `cpick` / `cpurge` for Claude Code conversations |
| claude-desktop | Claude Desktop from Anthropic's signed repository, updated silently |
| vscode | VS Code from Microsoft's signed repository, updated silently |
| jupyter | JupyterLab as a desktop app with a tray icon (needs Anaconda) |
| ticktick | TickTick launcher (you install the app) |
| login-screen | SDDM theme that matches the lock screen |
| firewall | nftables: nothing gets in unless you started it |
| zram | Compressed swap in RAM |

What the installer does:
- **Files are copied, not linked**, so you can change them. If you already have one, it goes to
  `~/.local/state/dotfiles-backup/<date>/` first, and my home path is replaced by yours.
- **Missing packages** are listed and installed with pacman if you say yes. Files in `/etc` and
  services are each asked or listed too.
- **Updating:** run it again. Your `~/.config/hypr/local.lua` is never touched.

Other options: `install --list`, `--only core,terminal`, `--all`, `--dry-run` (shows what would
change), `--no-packages`, `--no-services`. Parts and their files: [`.config/dotfiles/components`](../.config/dotfiles/components).

### After installing
1. Log in to **Hyprland (uwsm-managed)**.
2. Set a wallpaper; the whole theme follows it: `wallpaper ~/Pictures/image.jpg`
3. Put your screen, keyboard layout and own shortcuts in **`~/.config/hypr/local.lua`**. If you had a `hyprland.conf`, Hyprland now ignores it (it reads `hyprland.lua`), so move what you need from it into `local.lua`. The
   installer writes a starting version with your keyboard layout.
4. Optional: for the night light's sunset times, put `latitude longitude` in `~/.config/hypr/location`.
5. **Super + I** lists every shortcut. The full guide is [`.config/hypr/README.md`](../.config/hypr/README.md) ([PDF](../.config/hypr/README.pdf)).

## Where things are

| Path | What |
|---|---|
| [`.config/hypr/`](../.config/hypr) | `hyprland.lua` (shared), `local.lua` (each person's own), `workspaces.lua`, lock and idle, the guide |
| [`.config/hypr/scripts/`](../.config/hypr/scripts) | Spotlight, theme, screenshot, night light, menus · [`panels/`](../.config/hypr/scripts/panels): the bar's panels and the screenshot tool (Python + GTK4) |
| [`.config/waybar/`](../.config/waybar), [`.config/rofi/`](../.config/rofi), [`.config/swaync/`](../.config/swaync) | Bar, menus, notifications (`colors.*` are generated from the wallpaper) |
| [`.config/systemd/user/`](../.config/systemd/user) | Services: bar, Spotlight, panels, wallpaper, idle, night light, battery watch, updaters |
| [`.config/dotfiles/`](../.config/dotfiles) | The installer and its list of parts |
| [`.local/bin/`](../.local/bin) | `wallpaper`, `caffeinate`, the updaters, launchers |
| [`.config/system-config/`](../.config/system-config) | Copies of files in `/etc` (firewall, zram, login screen) and my package lists |
| `.config/refind/`, `.bashrc`, `.config/mimeapps.list`, `.config/autostart/` | Mine only: the installer never copies them |

## How I use it (the owner)

This repo is a **bare git repo**: the files stay where they live in my `$HOME`, and git's data lives in
`~/.dotfiles`. [`dotfiles`](../.local/bin/dotfiles) is a small wrapper around git:

```bash
dotfiles status            # any git command works
dotfiles add ~/.config/foo # start tracking a file
dotfiles save "message"    # copy /etc files and package lists, scan for secrets, commit, push
```

Every commit is checked for secrets first ([`dotfiles-scan`](../.local/bin/dotfiles-scan)). My own
fresh install uses a bare checkout plus [`.config/system-config/setup`](../.config/system-config/setup).

## Credits and licences

My own work here is under the [MIT licence](LICENSE). It doesn't cover the third-party parts below:

- Look based on [1amSimp1e/dots](https://github.com/1amSimp1e/dots) (GPL-3.0). The [Waybar](../.config/waybar) and [Rofi](../.config/rofi) files started from it and from [adi1090x/rofi](https://github.com/adi1090x/rofi) (GPL-3.0), so they are not under MIT.
- Font: Paper Mono by the [Paper Mono project](https://github.com/paper-design/paper-mono), with [Nerd Fonts](https://www.nerdfonts.com) icons added: SIL Open Font License 1.1, see [`OFL.txt`](../.local/share/fonts/PaperMono-Nerd/OFL.txt).
- Icons: [Font Awesome Free](https://fontawesome.com) (Arch package `otf-font-awesome`, not included here).
- My wallpaper: photo by Arnaud Mariat on [Unsplash](https://unsplash.com/photos/45Z6hW1dQMI). The repo only holds a link to my local file, not the photo.
- [Brad's rEFInd theme](https://github.com/toptensoftware/brads-refind-theme) by Topten Software: Apache 2.0, see its [`readme.md`](../.config/refind/themes/brads-refind-theme/readme.md).
- Third-party apps belong to their authors.
