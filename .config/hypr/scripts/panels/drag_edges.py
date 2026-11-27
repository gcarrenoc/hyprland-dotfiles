"""Drag a file (or text, an image, a link…) to the left / right edge of the screen and hold it there:
the previous / next workspace comes up, so you can drop it in an app over there — like macOS.

Wayland only tells a window "something is being dragged over you" during a real drag-and-drop; a
plain click-and-drag (selecting text, a slider, a scrollbar) never reaches it. So the edges are two
invisible 2-px strips per screen that exist only while the left button is down (Hyprland's click hooks
in hyprland.lua show / hide them) and react only to drag-and-drop. They never take a drop or a click.
An edge shared with another screen isn't used: dragging across it simply goes to that screen.

The bar works the same way: drag something over a workspace button on the bar, it lights up, and after
a moment that workspace comes up. Waybar doesn't say where its buttons are, but it tells the
accessibility bus (AT-SPI), like any GTK app tells a screen reader: name "3 …" and position.
Clicks that start on the bar don't show any of this (hyprland.lua), so the bar's own clicks are untouched.
"""
import json, os, re, subprocess, threading

from base import Gdk, GLib, Gtk, Layer

WIDTH = 2           # px at the very edge (the cursor stops there)
HOLD = 450          # ms hovering at the edge before the first switch
AGAIN = 900         # ms for each further switch while still there

SPRING = 500        # ms hovering a workspace button on the bar before going there
LIMIT = 60          # s: the strips never stay up longer (a lost "button up" can't leave them in the way)

# alpha 1/255: invisible, but not "nothing" — a window that draws nothing at all is never shown
CSS = ("window.dragedge { background: rgba(0, 0, 0, 0.004); box-shadow: none; border: none; }"
       " window.dragedge > * { background: none; }"
       " window.dragedge .dropspot { background: rgba(255, 255, 255, 0.22); border-radius: 8px;"
       " box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.45); }")


def flip(d):
    """Show the workspace d steps away on this screen (only existing ones: see WS.flip)."""
    subprocess.Popen(["hyprctl", "dispatch", f"function() WS.flip({d}) end"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def go(n):
    subprocess.Popen(["hyprctl", "dispatch", f"function() WS.go({n}) end"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def waybar_buttons(connector):
    """[(workspace, x, width, y, height)] of the workspace buttons on this screen's bar, from AT-SPI.
    Blocking D-Bus calls: run it off the GTK main loop (this app is on the bus too and must stay free to answer)."""
    try:
        import gi
        gi.require_version("Atspi", "2.0")
        from gi.repository import Atspi
    except (ImportError, ValueError):
        return []
    bars = []
    desk = Atspi.get_desktop(0)
    for i in range(desk.get_child_count()):
        app = desk.get_child_at_index(i)
        if not app or app.get_process_id() == os.getpid() or app.get_name() != "waybar":
            continue
        for f in range(app.get_child_count()):
            found = []

            def walk(o, depth):
                if depth > 10 or o is None:
                    return
                if o.get_role_name() == "button":
                    m = re.match(r"\s*(\d+)\b", o.get_name() or "")
                    if m:
                        e = o.get_extents(Atspi.CoordType.WINDOW)
                        found.append((int(m.group(1)), e.x, e.width, e.y, e.height))
                    return
                for k in range(o.get_child_count()):
                    walk(o.get_child_at_index(k), depth + 1)

            walk(app.get_child_at_index(f), 0)
            if found:
                bars.append(found)
    if len(bars) <= 1:
        return bars[0] if bars else []
    try:                                                     # several screens: the bar showing this screen's workspaces
        mine = {w["id"] for w in json.loads(subprocess.run(["hyprctl", "workspaces", "-j"], capture_output=True,
                                                           text=True).stdout) if w["monitor"] == connector}
    except ValueError:
        mine = set()
    return max(bars, key=lambda b: len(mine & {n for n, *_ in b}))


class BarStrip(Gtk.Window):
    """Invisible layer over the bar while the button is down; lights up the workspace button a drag is over."""
    def __init__(self, app, monitor, height):
        super().__init__(application=app, title="drag-bar", decorated=False)
        self.add_css_class("dragedge")
        self.connector, self.buttons, self.under, self.timer = monitor.get_connector(), [], None, 0
        Layer.init_for_window(self)
        Layer.set_namespace(self, "drag-edge")
        Layer.set_layer(self, Layer.Layer.OVERLAY)
        Layer.set_monitor(self, monitor)
        for edge in (Layer.Edge.TOP, Layer.Edge.LEFT, Layer.Edge.RIGHT):
            Layer.set_anchor(self, edge, True)
        Layer.set_exclusive_zone(self, -1)
        Layer.set_keyboard_mode(self, Layer.KeyboardMode.NONE)
        self.set_default_size(-1, height)
        self.fixed = Gtk.Fixed(height_request=height)
        self.spot = Gtk.Box(css_classes=["dropspot"], visible=False)
        self.fixed.put(self.spot, 0, 0)
        self.set_child(self.fixed)
        motion = Gtk.DropControllerMotion()
        motion.connect("enter", self.enter)
        motion.connect("motion", self.motion)
        motion.connect("leave", lambda *_: self.reset())
        self.add_controller(motion)

    def enter(self, _c, x, y):
        self.x, self.buttons = x, []
        def look():                                           # where the buttons are right now (~15 ms)
            found = waybar_buttons(self.connector)
            GLib.idle_add(lambda: (setattr(self, "buttons", found), self.motion(None, self.x, 0)) and False)
        threading.Thread(target=look, daemon=True).start()

    def motion(self, _c, x, _y):
        self.x = x
        hit = next((b for b in self.buttons if b[1] <= x < b[1] + b[2]), None)
        if hit == self.under:
            return
        self.reset()
        self.under = hit
        if hit:
            n, bx, bw, by, bh = hit
            self.spot.set_size_request(bw, bh)
            self.fixed.move(self.spot, bx, by)
            self.spot.set_visible(True)
            self.timer = GLib.timeout_add(SPRING, self.fire)

    def fire(self):
        self.timer = 0
        if self.under:
            go(self.under[0])
        return False

    def reset(self):
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0
        self.under = None
        self.spot.set_visible(False)

    def hide(self):
        self.reset()
        self.set_visible(False)


class Strip(Gtk.Window):
    def __init__(self, app, monitor, d):
        super().__init__(application=app, title="drag-edge", decorated=False)
        self.add_css_class("dragedge")
        self.d, self.timer = d, 0
        Layer.init_for_window(self)
        Layer.set_namespace(self, "drag-edge")
        Layer.set_layer(self, Layer.Layer.OVERLAY)
        Layer.set_monitor(self, monitor)
        for edge in (Layer.Edge.TOP, Layer.Edge.BOTTOM, Layer.Edge.LEFT if d < 0 else Layer.Edge.RIGHT):
            Layer.set_anchor(self, edge, True)
        Layer.set_exclusive_zone(self, -1)                   # over the bar too, reserves no space
        Layer.set_keyboard_mode(self, Layer.KeyboardMode.NONE)
        self.set_default_size(WIDTH, -1)
        self.set_child(Gtk.Box(width_request=WIDTH))
        motion = Gtk.DropControllerMotion()                  # only drag-and-drop, never plain pointer moves
        motion.connect("enter", self.enter)
        motion.connect("leave", lambda *_: self.cancel())
        self.add_controller(motion)

    def enter(self, *_):
        self.cancel()
        self.timer = GLib.timeout_add(HOLD, self.fire)

    def fire(self):
        flip(self.d)
        self.timer = GLib.timeout_add(AGAIN, self.fire)
        return False                                         # this one is done; the next is scheduled

    def cancel(self):
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0

    def hide(self):
        self.cancel()
        self.set_visible(False)


class DragEdges:
    def __init__(self, app):
        self.app, self.strips, self.layout = app, [], None
        self.ended, self.limit = [], 0                       # ids of clicks already released; safety timer
        css = Gtk.CssProvider()
        css.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)

    def build(self):
        """One strip per outer edge of each screen (rebuilt when screens change)."""
        mons = list(Gdk.Display.get_default().get_monitors())
        layout = [(m.get_connector(), m.get_geometry().x, m.get_geometry().y, m.get_geometry().width,
                   m.get_geometry().height) for m in mons]
        if layout == self.layout:
            return
        for s in self.strips:
            s.destroy()
        self.strips, self.layout = [], layout

        def shared(g, d):                                    # another screen touches this side
            x = g.x - 1 if d < 0 else g.x + g.width
            return any(o.get_geometry().x <= x < o.get_geometry().x + o.get_geometry().width
                       and o.get_geometry().y < g.y + g.height and g.y < o.get_geometry().y + o.get_geometry().height
                       for o in mons if o.get_geometry() != g)

        try:                                                 # the bar's height on each screen
            tops = {m["name"]: m["reserved"][1] for m in json.loads(subprocess.run(
                ["hyprctl", "monitors", "-j"], capture_output=True, text=True).stdout)}
        except (ValueError, KeyError, IndexError):
            tops = {}
        for m in mons:
            for d in (-1, 1):
                if not shared(m.get_geometry(), d):
                    self.strips.append(Strip(self.app, m, d))
            if tops.get(m.get_connector(), 0) > 0:
                self.strips.append(BarStrip(self.app, m, int(tops[m.get_connector()])))

    def start(self, click):
        """Button down. A tap can deliver its release first: then this press is already over."""
        if click in self.ended:
            return
        self.show()

    def end(self, click):
        self.ended = (self.ended + [click])[-16:]
        self.hide()

    def show(self):
        self.build()
        for s in self.strips:
            s.set_visible(True)
        if self.limit:
            GLib.source_remove(self.limit)
        self.limit = GLib.timeout_add_seconds(LIMIT, lambda: self.hide() or False)

    def hide(self):
        if self.limit:
            GLib.source_remove(self.limit)
            self.limit = 0
        for s in self.strips:
            s.hide()
