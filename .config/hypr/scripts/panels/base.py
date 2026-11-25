"""What the bar's panels share: look, helpers and a window that drops down under the bar."""
import json, re, subprocess, threading, time
from ctypes import CDLL
from pathlib import Path

CDLL("libgtk4-layer-shell.so.0")                          # has to be loaded before GTK
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gdk, Gio, GLib, Gtk, Gtk4LayerShell as Layer, Pango

COLORS = Path.home() / ".config/rofi/colors.rasi"
WIDTH = 340
# Lucide glyphs (codepoints: ~/.local/share/fonts/Lucide/codepoints.json)
G = {k: chr(v) for k, v in {
    "vol0": 0xe1a9, "vol1": 0xe1aa, "vol2": 0xe1ab, "muted": 0xe1ac, "mic": 0xe118, "micoff": 0xe119,
    "headphones": 0xe0f1, "speaker": 0xe1cd, "screen": 0xe11d, "bluetooth": 0xe05c, "usb": 0xe356,
    "check": 0xe06c, "play": 0xe13c, "pause": 0xe12e, "prev": 0xe15f, "next": 0xe160, "sliders": 0xe29a,
    "wifi0": 0xe5f9, "wifi1": 0xe5f8, "wifi2": 0xe5f7, "wifi3": 0xe1ae, "wifioff": 0xe1af, "lock": 0xe10b,
    "cable": 0xe620, "shield": 0xe158, "globe": 0xe0e8,
    "battery": 0xe053, "charging": 0xe054, "full": 0xe055, "low": 0xe056, "medium": 0xe057, "plug": 0xe37f,
    "btoff": 0xe1b9, "more": 0xe0b6, "keyboard": 0xe284, "mouse": 0xe28e, "gamepad": 0xe0df, "phone": 0xe163,
    "printer": 0xe141, "watch": 0xe1ad, "loudspeaker": 0xe166, "sun": 0xe178, "moon": 0xe11e, "warm": 0xe186,
    "coffee": 0xe096, "auto": 0xe357,
    "leaf": 0xe2de, "scale": 0xe212, "rocket": 0xe286,
}.items()}


def out(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def launch(*cmd):
    subprocess.Popen(["uwsm", "app", "--", *cmd], start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def theme_css():
    c = dict(re.findall(r"^\s*([\w-]+):\s*(#[0-9a-fA-F]{6,8});", COLORS.read_text(), re.M)) if COLORS.exists() else {}
    def rgba(key, default, alpha=None):
        h = c.get(key, default).lstrip("#")
        a = alpha if alpha is not None else (int(h[6:8], 16) / 255 if len(h) == 8 else 1)
        return f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, {a:.3f})"
    bg, fg = rgba("background", "#dbdfebb3"), rgba("foreground", "#161b2d")
    sel, on_sel = rgba("selected", "#3e528e"), rgba("on-selected", "#ffffff")
    muted, border = rgba("muted", "#343b51"), rgba("active", "#c6cbdd")
    card = rgba("background-alt", "#f2f3f8", 0.62)
    field, urgent = rgba("background-alt", "#f2f3f8", 0.9), rgba("urgent", "#be3742")
    return f"""
    window.barpanel {{ background: none; }}
    window.barpanel * {{ font-family: "PaperMono Nerd Font"; font-size: 11pt; }}
    .panel {{ background-color: {bg}; backdrop-filter: blur(20px); color: {fg};
              border: 1px solid {border}; border-radius: 19px; padding: 12px; }}
    .panel label.lucide {{ font-family: lucide; font-size: 14pt; }}
    .card {{ background-color: {card}; border-radius: 13px; padding: 8px 10px; }}
    .head {{ color: {muted}; font-size: 9pt; font-weight: bold; padding: 0 2px; }}
    .note, .value {{ color: {muted}; font-size: 9.5pt; }}
    .title {{ font-weight: bold; }}
    .panel button {{ background: none; border: none; box-shadow: none; outline: none; color: {fg};
                     min-height: 0; min-width: 0; padding: 4px 6px; border-radius: 9px; }}
    .panel button:hover {{ background-color: alpha({sel}, 0.14); }}
    .panel button:focus-visible {{ background-color: alpha({sel}, 0.14); }}
    .panel button.device {{ padding: 5px 8px; }}
    .panel button.device.on {{ background-color: {sel}; color: {on_sel}; }}
    .panel button.device.on label {{ color: {on_sel}; }}
    .panel button.off label {{ color: {muted}; }}
    .panel scale {{ padding: 4px 0; margin: 0 6px; min-height: 0; }}
    .panel scale trough {{ min-height: 8px; border-radius: 6px; background-color: alpha({fg}, 0.16); border: none; }}
    .panel scale highlight {{ min-height: 8px; border-radius: 6px; background: {sel}; border: none; margin: 0; }}
    .panel scale slider {{ min-width: 16px; min-height: 16px; margin: -5px; border-radius: 9px;
                           background: {on_sel}; border: 1px solid alpha({fg}, 0.25); box-shadow: none; }}
    .panel scale.off highlight {{ background: alpha({muted}, 0.45); }}
    .panel button.row {{ padding: 5px 8px; }}
    .panel button.row.on {{ background-color: {sel}; color: {on_sel}; }}
    .panel button.row.on label {{ color: {on_sel}; }}
    .panel button.action {{ background-color: alpha({sel}, 0.14); padding: 4px 12px; }}
    .panel button.action:hover {{ background-color: {sel}; color: {on_sel}; }}
    .panel button.action:hover label {{ color: {on_sel}; }}
    .panel .error {{ color: {urgent}; font-size: 9.5pt; font-weight: bold; }}
    .panel entry, .panel passwordentry, .panel entry > text, .panel passwordentry > text {{ color: {fg}; caret-color: {fg}; }}
    .panel entry, .panel passwordentry {{ background-color: {field}; border: 1px solid alpha({fg}, 0.2); border-radius: 9px;
                            padding: 4px 8px; min-height: 0; outline: none; box-shadow: none; }}
    .panel switch {{ background: alpha({fg}, 0.25); border: none; border-radius: 12px; min-height: 22px; outline: none; }}
    .panel switch:checked {{ background: {sel}; }}
    .panel switch > slider {{ background: {on_sel}; border: none; box-shadow: none; border-radius: 10px;
                              min-width: 18px; min-height: 18px; margin: 2px; }}
    .panel progressbar trough, .panel progressbar progress {{ min-height: 8px; min-width: 0; border-radius: 6px; border: none; }}
    .panel progressbar trough {{ background: alpha({fg}, 0.16); }}
    .panel progressbar progress {{ background: {sel}; }}
    .panel progressbar.low progress {{ background: {urgent}; }}
    .panel spinner {{ color: {sel}; min-width: 16px; min-height: 16px; }}
    .panel scrolledwindow {{ border-radius: 13px; }}
    .panel scrollbar {{ background: none; border: none; }}
    scrolledwindow, viewport {{ background: none; }}
    """


def box(vertical=True, spacing=6, **kw):
    return Gtk.Box(orientation=Gtk.Orientation.VERTICAL if vertical else Gtk.Orientation.HORIZONTAL,
                   spacing=spacing, **kw)


def lucide(name):
    return Gtk.Label(label=G[name], css_classes=["lucide"], width_chars=2)


def text(s, cls=None, expand=True):
    return Gtk.Label(label=s, xalign=0, hexpand=expand, ellipsize=Pango.EllipsizeMode.END,
                     css_classes=[cls] if cls else [])


def button(child, tip, action, *classes):
    b = Gtk.Button(child=child, tooltip_text=tip, css_classes=list(classes))
    b.connect("clicked", lambda *_: action())
    return b


class Commands(threading.Thread):
    """Runs commands one at a time; while a slider is dragged only its newest value is sent."""
    def __init__(self):
        super().__init__(daemon=True)
        self.todo, self.cond = {}, threading.Condition()
        self.start()

    def send(self, key, *cmd):
        with self.cond:
            self.todo.pop(key, None)
            self.todo[key] = cmd
            self.cond.notify()

    def run(self):
        while True:
            with self.cond:
                while not self.todo:
                    self.cond.wait()
                cmd = self.todo.pop(next(iter(self.todo)))
            out(*cmd)


class DropPanel(Gtk.ApplicationWindow):
    """Transparent layer over the screen below the bar with one frosted card: a click outside closes it."""
    def __init__(self, app, name):
        super().__init__(application=app, title=name, decorated=False)
        self.add_css_class("barpanel")
        self.hidden_at = 0.0
        Layer.init_for_window(self)
        Layer.set_namespace(self, f"{name}-panel")
        Layer.set_layer(self, Layer.Layer.TOP)
        for edge in (Layer.Edge.TOP, Layer.Edge.BOTTOM, Layer.Edge.LEFT, Layer.Edge.RIGHT):
            Layer.set_anchor(self, edge, True)
        Layer.set_keyboard_mode(self, Layer.KeyboardMode.EXCLUSIVE)     # typing and Esc while it's open

        self.panel = box(spacing=8, css_classes=["panel"], halign=Gtk.Align.START, valign=Gtk.Align.START, margin_top=4)
        self.panel.set_size_request(WIDTH, -1)
        self.set_child(self.panel)
        click = Gtk.GestureClick(button=0)
        click.connect("pressed", self.clicked)
        self.add_controller(click)
        keys = Gtk.EventControllerKey()
        keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self.key)
        self.add_controller(keys)
        self.connect("close-request", lambda w: w.dismiss() or True)    # hide, never destroy

    def clicked(self, _g, _n, x, y):
        hit = self.pick(x, y, Gtk.PickFlags.DEFAULT)
        if hit is None or not (hit == self.panel or hit.is_ancestor(self.panel)):
            self.dismiss()

    def key(self, _c, val, _code, _mods):
        if val == Gdk.KEY_Escape:
            self.dismiss()
            return True
        return False

    def place(self):
        """Under the pointer (= under the volume icon), inside the screen; else top right."""
        width = None
        try:
            mons = json.loads(out("hyprctl", "monitors", "-j"))
            mon = next(m for m in mons if m["focused"])
            width = mon["width"] / mon["scale"] if mon["transform"] % 2 == 0 else mon["height"] / mon["scale"]
            pos = json.loads(out("hyprctl", "cursorpos", "-j"))
            x, y = pos["x"] - mon["x"], pos["y"] - mon["y"]
        except (StopIteration, KeyError, ValueError):
            x, y = 0, 999
        width = width or 1536
        left = x - WIDTH / 2 if y < 40 else width - WIDTH - 6
        self.panel.set_margin_start(int(max(6, min(left, width - WIDTH - 6))))

    def toggle(self):
        if self.get_visible():
            self.dismiss()
        elif time.monotonic() - self.hidden_at > 0.25:         # else: this same click just closed it
            self.place()
            self.open()

    def dismiss(self):
        self.set_visible(False)
        self.hidden_at = time.monotonic()

    def clear(self, parent=None):
        parent = parent or self.panel
        while (w := parent.get_first_child()) is not None:
            parent.remove(w)

    def section(self, name):
        self.panel.append(text(name, "head"))
        card = box(spacing=4, css_classes=["card"])
        self.panel.append(card)
        return card
