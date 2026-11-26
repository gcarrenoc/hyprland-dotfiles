"""Screenshot overlay (Print), like GNOME's: the screen freezes and dims, and you choose.

  Selection   drag an area; drag inside it to move it, its edges or corners to resize (it's remembered)
  Screen      the whole screen you're on
  Window      click a window (it's captured on its own, even if something covers it, with its rounded corners)
  Photo / video switch: a screenshot, or a screen recording (stop it with the red dot on the bar,
  or Print again)
  Pointer     include the mouse pointer (screenshots)

  Enter / Space capture · Esc close · S selection · C screen · W window · V video · P pointer

No coloured window borders in the pictures. Screenshots: ~/Pictures/Screenshots, also copied to the clipboard; the notification opens, edits
(swappy) or shows it in Files. Recordings: ~/Videos/Screencasts (wf-recorder).
"""
import json, os, shutil, subprocess, threading, time
from pathlib import Path
import gi
gi.require_version("Graphene", "1.0")
gi.require_version("Gsk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from base import G, Gdk, GLib, Gtk, Layer, box, out
from gi.repository import GdkPixbuf, Graphene, Gsk

PICTURES = Path(subprocess.run(["xdg-user-dir", "PICTURES"], capture_output=True, text=True).stdout.strip()
                or Path.home() / "Pictures") / "Screenshots"
VIDEOS = Path(subprocess.run(["xdg-user-dir", "VIDEOS"], capture_output=True, text=True).stdout.strip()
              or Path.home() / "Videos") / "Screencasts"
BAR_PIPE = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "bar-state"
HANDLE = 14                                               # how near an edge counts as grabbing it (px)
MIN = 8


def rgba(r, g, b, a):
    c = Gdk.RGBA(); c.red, c.green, c.blue, c.alpha = r, g, b, a
    return c


def rect(x, y, w, h):
    return Graphene.Rect().init(x, y, w, h)


def tell_bar():
    try:
        fd = os.open(BAR_PIPE, os.O_WRONLY | os.O_NONBLOCK)
        os.write(fd, b"r\n"); os.close(fd)
    except OSError:
        pass


def borders(show):
    """Hyprland's window borders: hidden (transparent, nothing moves) while a frame is taken. hyprland.lua: Borders()"""
    subprocess.run(["hyprctl", "dispatch", f"function() Borders({'true' if show else 'false'}) end"], capture_output=True)
    if not show:
        time.sleep(0.05)                                      # one frame drawn without them


def recording():
    return subprocess.run(["pgrep", "-x", "wf-recorder"], capture_output=True).returncode == 0


def stop_recording():
    subprocess.run(["pkill", "-INT", "-x", "wf-recorder"], capture_output=True)


class Canvas(Gtk.Widget):
    """The frozen screen, dimmed outside what will be captured, with the selection's frame."""
    def __init__(self, shot):
        super().__init__(hexpand=True, vexpand=True)
        self.shot = shot

    def do_snapshot(self, snap):
        s, W, H = self.shot, self.get_width(), self.get_height()
        if s.texture is None:
            return
        snap.append_texture(s.texture, rect(0, 0, W, H))
        dark = rgba(0, 0, 0, 0.5)
        r = s.target()
        if r is None:
            snap.append_color(dark, rect(0, 0, W, H))
            return
        x, y, w, h = r
        for part in ((0, 0, W, y), (0, y + h, W, H - y - h), (0, y, x, h), (x + w, y, W - x - w, h)):
            if part[2] > 0 and part[3] > 0:
                snap.append_color(dark, rect(*part))
        if s.mode == "screen":
            return
        white = rgba(1, 1, 1, 0.95)
        for edge in ((x - 2, y - 2, w + 4, 2), (x - 2, y + h, w + 4, 2), (x - 2, y, 2, h), (x + w, y, 2, h)):
            snap.append_color(white, rect(*edge))
        if s.mode == "selection":                         # round handles on the corners
            for cx, cy in ((x, y), (x + w, y), (x, y + h), (x + w, y + h)):
                rr = Gsk.RoundedRect(); rr.init_from_rect(rect(cx - 6, cy - 6, 12, 12), 6)
                snap.push_rounded_clip(rr); snap.append_color(white, rect(cx - 6, cy - 6, 12, 12)); snap.pop()


class ScreenshotOverlay(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Screenshot", decorated=False)
        self.add_css_class("shotwin")
        Layer.init_for_window(self)
        Layer.set_namespace(self, "screenshot")
        Layer.set_layer(self, Layer.Layer.OVERLAY)
        for edge in (Layer.Edge.TOP, Layer.Edge.BOTTOM, Layer.Edge.LEFT, Layer.Edge.RIGHT):
            Layer.set_anchor(self, edge, True)
        Layer.set_exclusive_zone(self, -1)                # over the bar too
        Layer.set_keyboard_mode(self, Layer.KeyboardMode.EXCLUSIVE)
        self.mode, self.video, self.pointer = "selection", False, False
        self.sel, self.remembered = None, {}
        self.texture = self.frames = self.monitor = None
        self.windows, self.hover, self.chosen = [], None, None
        self.drag = None

        overlay = Gtk.Overlay()
        self.canvas = Canvas(self)
        overlay.set_child(self.canvas)
        self.size = Gtk.Label(css_classes=["shotsize"], halign=Gtk.Align.START, valign=Gtk.Align.START)
        self.size.set_can_target(False)
        overlay.add_overlay(self.size)
        overlay.add_overlay(self.toolbar())
        close = Gtk.Button(child=Gtk.Label(label="", css_classes=["icon"]), css_classes=["shotclose"],
                           halign=Gtk.Align.END, valign=Gtk.Align.START, margin_top=18, margin_end=18,
                           tooltip_text="Close (Esc)")
        close.connect("clicked", lambda *_: self.dismiss())
        overlay.add_overlay(close)
        self.set_child(overlay)

        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", self.begin); drag.connect("drag-update", self.update); drag.connect("drag-end", self.end)
        self.canvas.add_controller(drag)
        move = Gtk.EventControllerMotion()
        move.connect("motion", self.moved)
        self.canvas.add_controller(move)
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self.key)
        self.add_controller(keys)
        self.connect("close-request", lambda w: w.dismiss() or True)

    # ----- the floating toolbar
    def toolbar(self):
        bar = box(False, 14, css_classes=["shotbar"], halign=Gtk.Align.CENTER, valign=Gtk.Align.END, margin_bottom=36)
        modes = box(False, 4, css_classes=["shotgroup"])
        self.modebtn = {}
        for key, glyph, label, tip in (("selection", "", "Selection", "S"), ("screen", "", "Screen", "C"),
                                       ("window", "", "Window", "W")):
            inner = box(True, 3)
            inner.append(Gtk.Label(label=glyph, css_classes=["icon"])); inner.append(Gtk.Label(label=label, css_classes=["shotlabel"]))
            b = Gtk.Button(child=inner, css_classes=["shotmode"], tooltip_text=f"{label} ({tip})")
            b.connect("clicked", lambda _b, k=key: self.set_mode(k))
            self.modebtn[key] = b
            modes.append(b)
        bar.append(modes)
        self.shutter = Gtk.Button(css_classes=["shutter"], tooltip_text="Capture (Enter)", valign=Gtk.Align.CENTER)
        self.shutter.set_child(Gtk.Box(css_classes=["shutterdot"], halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER))
        self.shutter.connect("clicked", lambda *_: self.capture())
        bar.append(self.shutter)
        kind = box(False, 4, css_classes=["shotgroup"])
        self.photo = Gtk.Button(child=Gtk.Label(label="", css_classes=["icon"]), css_classes=["shotmode"], tooltip_text="Screenshot")
        self.film = Gtk.Button(child=Gtk.Label(label="", css_classes=["icon"]), css_classes=["shotmode"], tooltip_text="Screen recording (V)")
        self.photo.connect("clicked", lambda *_: self.set_video(False))
        self.film.connect("clicked", lambda *_: self.set_video(True))
        kind.append(self.photo); kind.append(self.film)
        bar.append(kind)
        self.cursor = Gtk.ToggleButton(child=Gtk.Label(label="", css_classes=["icon"]), css_classes=["shotmode"],
                                       tooltip_text="Include the pointer (P)")
        self.cursor.connect("toggled", lambda b: self.set_pointer(b.get_active()))
        bar.append(self.cursor)
        return bar

    def refresh(self):
        for k, b in self.modebtn.items():
            (b.add_css_class if k == self.mode else b.remove_css_class)("on")
        for b, on in ((self.photo, not self.video), (self.film, self.video)):
            (b.add_css_class if on else b.remove_css_class)("on")
        (self.shutter.add_css_class if self.video else self.shutter.remove_css_class)("video")
        self.cursor.set_sensitive(not self.video)
        r = self.target()
        if r and self.mode != "screen":
            x, y, w, h = r
            s = self.monitor["scale"]
            self.size.set_label(f"{round(w * s)} × {round(h * s)}")
            self.size.set_margin_start(int(max(4, x)))
            self.size.set_margin_top(int(y + h + 8 if y + h + 40 < self.get_height() else max(4, y - 32)))
            self.size.set_visible(True)
        else:
            self.size.set_visible(False)
        self.canvas.queue_draw()

    def set_mode(self, mode):
        self.mode, self.hover = mode, None
        if mode == "window" and self.chosen is None and self.windows:
            self.chosen = self.windows[0]                    # the window you were in
        self.refresh()

    def set_video(self, on):
        if on and not shutil.which("wf-recorder"):
            subprocess.Popen(["notify-send", "-a", "Screenshot", "Screen recording needs wf-recorder", "sudo pacman -S wf-recorder"])
            return
        self.video = on
        self.refresh()

    def set_pointer(self, on):
        self.pointer = on
        if self.frames:
            self.texture = self.frames[1 if on else 0][1]
        self.refresh()

    # ----- open / close
    def focused(self):
        try:
            return next(m for m in json.loads(out("hyprctl", "monitors", "-j")) if m["focused"])
        except (StopIteration, ValueError):
            return None

    def toggle(self):
        if recording():                                       # Print while recording: stop it
            stop_recording()
            return
        if self.get_visible():
            self.dismiss()
            return
        mon = self.focused()
        if not mon:
            return
        frames, grabs = [], []
        borders(False)                                        # no coloured window borders in the picture
        try:
            for cursor in (False, True):                      # freeze the screen first, before anything is shown
                grabs.append(subprocess.run(["grim", "-l", "1", "-o", mon["name"], *(["-c"] if cursor else []), "-"],
                                            capture_output=True).stdout)
        finally:
            borders(True)
        for png in grabs:
            if not png:
                subprocess.Popen(["notify-send", "-a", "Screenshot", "Couldn't capture the screen"])
                return
            loader = GdkPixbuf.PixbufLoader.new_with_type("png"); loader.write(png); loader.close()
            pix = loader.get_pixbuf()
            frames.append((pix, Gdk.Texture.new_for_pixbuf(pix)))
        self.monitor, self.frames = mon, frames
        self.texture = frames[1 if self.pointer else 0][1]
        for m in Gdk.Display.get_default().get_monitors():
            if m.get_connector() == mon["name"]:
                Layer.set_monitor(self, m)
        self.windows = self.find_windows(mon)
        self.chosen, self.hover = (self.windows[0] if self.windows else None), None
        w, h = self.logical()
        self.sel = self.remembered.get((w, h)) or (w * 0.3, h * 0.3, w * 0.4, h * 0.4)
        self.present()
        self.refresh()

    def logical(self):
        m = self.monitor
        w, h = (m["width"], m["height"]) if m["transform"] % 2 == 0 else (m["height"], m["width"])
        return w / m["scale"], h / m["scale"]

    def find_windows(self, mon):
        try:
            clients = json.loads(out("hyprctl", "clients", "-j"))
        except ValueError:
            return []
        shown = {mon["activeWorkspace"]["id"], mon.get("specialWorkspace", {}).get("id")}
        wins = [c for c in clients if c.get("mapped") and not c.get("hidden") and c["workspace"]["id"] in shown]
        wins.sort(key=lambda c: c.get("focusHistoryID", 99))       # the one you were in first, then the ones under it
        for c in wins:
            c["box"] = (c["at"][0] - mon["x"], c["at"][1] - mon["y"], c["size"][0], c["size"][1])
        return wins

    def dismiss(self):
        if self.sel and self.monitor:
            self.remembered[self.logical()] = self.sel
        self.set_visible(False)
        self.texture = self.frames = None                     # free the frozen frames

    # ----- what will be captured, in logical px on this screen
    def target(self):
        if self.mode == "screen":
            w, h = self.logical()
            return (0, 0, w, h)
        if self.mode == "window":
            c = self.hover or self.chosen
            return c["box"] if c else None
        return self.sel

    def window_at(self, x, y):
        for c in self.windows:
            bx, by, bw, bh = c["box"]
            if bx <= x < bx + bw and by <= y < by + bh:
                return c
        return None

    # ----- mouse
    def grip(self, x, y):
        """What a press at x, y would grab: a corner / edge of the selection, its inside, or nothing."""
        sx, sy, sw, sh = self.sel
        near = lambda a, b: abs(a - b) <= HANDLE
        inside_x, inside_y = sx - HANDLE <= x <= sx + sw + HANDLE, sy - HANDLE <= y <= sy + sh + HANDLE
        if not (inside_x and inside_y):
            return None
        edges = ("w" if near(x, sx) else "e" if near(x, sx + sw) else "") + ("n" if near(y, sy) else "s" if near(y, sy + sh) else "")
        if edges:
            return edges
        return "move" if sx < x < sx + sw and sy < y < sy + sh else None

    def moved(self, _c, x, y):
        if self.mode == "window":
            hit = self.window_at(x, y)
            if hit is not self.hover:
                self.hover = hit
                self.refresh()
            return
        if self.mode == "selection" and self.drag is None:
            g = self.grip(x, y)
            names = {"move": "move", "n": "n-resize", "s": "s-resize", "e": "e-resize", "w": "w-resize",
                     "ne": "ne-resize", "nw": "nw-resize", "se": "se-resize", "sw": "sw-resize"}
            self.canvas.set_cursor_from_name(names.get(g, "crosshair"))

    def begin(self, _g, x, y):
        if self.mode == "window":
            self.chosen = self.window_at(x, y) or self.chosen
            self.drag = ("click", x, y)
            self.refresh()
            return
        if self.mode == "screen":
            self.mode = "selection"                           # dragging on the screen: make a selection
        g = self.grip(x, y)
        self.drag = (g or "new", x, y, self.sel)

    def update(self, _g, dx, dy):
        if not self.drag or self.drag[0] == "click":
            return
        kind, x0, y0, (sx, sy, sw, sh) = self.drag
        W, H = self.logical()
        if kind == "new":
            x1, y1 = x0 + dx, y0 + dy
            self.sel = (min(x0, x1), min(y0, y1), abs(dx), abs(dy))
        elif kind == "move":
            self.sel = (min(max(0, sx + dx), W - sw), min(max(0, sy + dy), H - sh), sw, sh)
        else:
            l, t, r, b = sx, sy, sx + sw, sy + sh
            if "w" in kind: l = min(sx + dx, r - MIN)
            if "e" in kind: r = max(sx + sw + dx, l + MIN)
            if "n" in kind: t = min(sy + dy, b - MIN)
            if "s" in kind: b = max(sy + sh + dy, t + MIN)
            self.sel = (max(0, l), max(0, t), min(W, r) - max(0, l), min(H, b) - max(0, t))
        self.refresh()

    def end(self, *_):
        if self.drag and self.drag[0] == "new" and (self.sel[2] < MIN or self.sel[3] < MIN):
            self.sel = self.drag[3]                           # a click, not a drag: keep the old one
        self.drag = None
        self.refresh()

    # ----- keys
    def key(self, _c, val, _code, _mods):
        k = Gdk.keyval_to_lower(val)
        actions = {Gdk.KEY_Escape: self.dismiss, Gdk.KEY_Return: self.capture, Gdk.KEY_KP_Enter: self.capture,
                   Gdk.KEY_space: self.capture, Gdk.KEY_s: lambda: self.set_mode("selection"),
                   Gdk.KEY_c: lambda: self.set_mode("screen"), Gdk.KEY_w: lambda: self.set_mode("window"),
                   Gdk.KEY_v: lambda: self.set_video(not self.video),
                   Gdk.KEY_p: lambda: self.cursor.set_active(not self.cursor.get_active())}
        if k in actions:
            actions[k]()
            return True
        return False

    # ----- capture
    def capture(self):
        r = self.target()
        if not r or r[2] < 1 or r[3] < 1:
            return
        mon, mode, chosen = self.monitor, self.mode, (self.hover or self.chosen)
        stamp = time.strftime("%Y-%m-%d %H-%M-%S")
        if self.video:
            self.dismiss()
            self.record(mon, r, mode, chosen, stamp)
            return
        PICTURES.mkdir(parents=True, exist_ok=True)
        path = PICTURES / f"Screenshot From {stamp}.png"
        pix = self.frames[1 if self.pointer else 0][0]
        self.dismiss()
        if mode == "window" and chosen and not self.pointer:  # the window on its own, even if covered
            ok = subprocess.run(["grim", "-T", chosen.get("stableId", ""), str(path)], capture_output=True).returncode == 0
        else:
            ok = False
        if not ok:
            s = mon["scale"]
            x, y = max(0, round(r[0] * s)), max(0, round(r[1] * s))
            w, h = min(pix.get_width() - x, round(r[2] * s)), min(pix.get_height() - y, round(r[3] * s))
            pix.new_subpixbuf(x, y, w, h).savev(str(path), "png", [], [])
        if mode == "window":                                  # its rounded corners, as on screen
            subprocess.run([str(Path(__file__).resolve().parent.parent / "round-corners"), str(path), str(mon["scale"])],
                           capture_output=True)
        self.done(path, "Screenshot captured", "image/png")

    def record(self, mon, r, mode, chosen, stamp):
        VIDEOS.mkdir(parents=True, exist_ok=True)
        path = VIDEOS / f"Screencast From {stamp}.mp4"
        if mode == "screen":
            where = ["-o", mon["name"]]
        else:
            x, y, w, h = (chosen["box"] if mode == "window" and chosen else r)
            w, h = int(w) // 2 * 2, int(h) // 2 * 2           # the video encoder wants even sizes
            where = ["-g", f"{int(mon['x'] + x)},{int(mon['y'] + y)} {w}x{h}"]
        def run():
            proc = subprocess.Popen(["wf-recorder", *where, "-f", str(path)], stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            GLib.timeout_add(400, lambda: tell_bar() and False)
            proc.wait()
            tell_bar()
            if path.exists() and path.stat().st_size:
                GLib.idle_add(lambda: self.done(path, "Screen recording saved", None) and False)
        threading.Thread(target=run, daemon=True).start()

    def done(self, path, title, clip_type):
        if clip_type:
            with open(path, "rb") as f:
                subprocess.Popen(["wl-copy", "--type", clip_type], stdin=f)
        def ask():
            body = f"{'Copied to the clipboard · ' if clip_type else ''}{str(path.parent).replace(str(Path.home()), '~')}"
            acts = ["-A", "default=Open", "-A", "folder=Show in Files"] + (["-A", "edit=Edit"] if clip_type else [])
            r = subprocess.run(["notify-send", "-a", "Screenshot", "-i", str(path) if clip_type else "video-x-generic",
                                *acts, "--wait", title, body], capture_output=True, text=True)
            choice = r.stdout.strip()
            cmd = {"default": ["xdg-open", str(path)], "folder": ["nautilus", "--select", str(path)],
                   "edit": ["swappy", "-f", str(path), "-o", str(path)]}.get(choice)
            if cmd:
                subprocess.Popen(["uwsm", "app", "--", *cmd], start_new_session=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        threading.Thread(target=ask, daemon=True).start()
