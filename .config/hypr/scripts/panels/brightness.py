"""Brightness panel (under the bar's sun): screen brightness and night light.

  Brightness    the same scale as the keys' pop-up (never fully dark)
  Night light   on / off, warmth (right = warmer) and today's sunset / sunrise

Night light is scripts/nightlight (hyprsunset): on at sunset, off at sunrise; what you choose here
stays until the next one. Reads the screen and the night light only while open.
"""
import subprocess, threading, time
from pathlib import Path
from base import Commands, DropPanel, G, GLib, Gtk, box, lucide, text

LIGHT = Path("/sys/class/backlight/intel_backlight")
SCRIPTS = Path(__file__).resolve().parent.parent
NIGHT = str(SCRIPTS / "nightlight")
STATE = Path.home() / ".cache/nightlight"
WARM, COOL, STEP = 2500, 6000, 250                            # kelvin, as in scripts/nightlight


def brightness():
    try:
        return round(int((LIGHT / "brightness").read_text()) * 100 / int((LIGHT / "max_brightness").read_text()))
    except (OSError, ValueError, ZeroDivisionError):
        return None


def night():
    try:
        f = STATE.read_text().split()
        return f[0] == "1", int(f[1])
    except (OSError, ValueError, IndexError):
        return False, 4000


class BrightnessPanel(DropPanel):
    def __init__(self, app):
        super().__init__(app, "brightness")
        self.cmd, self.touched, self.timer, self.own = Commands(), {"light": 0.0, "warm": 0.0, "night": 0.0}, 0, False
        card = self.section("BRIGHTNESS")
        line = box(False, 6)
        line.append(lucide("sun"))
        self.light, self.light_num = self.slider(1, 100, 5, self.set_light, "Screen brightness")
        line.append(self.light); line.append(self.light_num)
        card.append(line)

        card = self.section("NIGHT LIGHT")
        line = box(False, 8)
        line.append(lucide("moon")); line.append(text("Night light", "title"))
        self.switch = Gtk.Switch(valign=Gtk.Align.CENTER, tooltip_text="Night light on / off")
        self.switch.connect("state-set", self.set_night)
        line.append(self.switch)
        card.append(line)
        line = box(False, 6)
        line.append(lucide("warm"))
        self.warm, self.warm_num = self.slider(0, COOL - WARM, STEP, self.set_warm, "Warmth (right = warmer)")
        line.append(self.warm); line.append(self.warm_num)
        card.append(line)
        self.sun = text("", "note")
        card.append(self.sun)

    @staticmethod
    def slider(low, high, step, moved, tip):
        s = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, low, high, step)
        s.set_draw_value(False); s.set_hexpand(True); s.set_tooltip_text(tip)
        s.connect("change-value", lambda _s, _t, v: moved(max(low, min(high, v))) and False)
        return s, Gtk.Label(width_chars=5, xalign=1, css_classes=["value"])

    def open(self):
        self.touched = dict.fromkeys(self.touched, 0.0)
        self.refresh()
        self.present()
        self.light.grab_focus()
        self.timer = GLib.timeout_add(400, lambda: self.refresh() or True)
        def times():
            try:
                f = subprocess.run([str(SCRIPTS / "suntimes")], capture_output=True, text=True, timeout=3).stdout.split()
                GLib.idle_add(self.sun.set_label, f"Automatic: on {f[2]}, off {f[1]}")
            except (OSError, subprocess.TimeoutExpired, IndexError):
                pass
        threading.Thread(target=times, daemon=True).start()

    def dismiss(self):
        super().dismiss()
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0

    def fresh(self, what, seconds=1.2):                       # just changed here: don't fight the hand
        return time.monotonic() - self.touched[what] < seconds

    def refresh(self):
        pct = brightness()
        self.light.set_sensitive(pct is not None)
        if pct is not None and not self.fresh("light", 0.6):
            self.light.set_value(pct)
            self.light_num.set_label(f"{pct}%")
        on, kelvin = night()
        if not self.fresh("night"):
            self.own = True
            self.switch.set_active(on)
            self.own = False
            self.warm.set_sensitive(on)
            (self.warm.remove_css_class if on else self.warm.add_css_class)("off")
        if not self.fresh("warm"):
            self.warm.set_value(COOL - kelvin)
            self.warm_num.set_label(f"{kelvin}K")

    def set_light(self, value):
        v = max(1, round(value))
        self.touched["light"] = time.monotonic()
        self.light_num.set_label(f"{v}%")
        self.cmd.send("light", "brightnessctl", "-q", "set", f"{v}%")

    def set_warm(self, value):
        kelvin = COOL - round(value / 50) * 50
        self.touched["warm"] = time.monotonic()
        self.warm_num.set_label(f"{kelvin}K")
        self.cmd.send("warm", NIGHT, "set", str(kelvin))

    def set_night(self, _switch, on):
        if not self.own:
            self.touched["night"] = time.monotonic()
            self.warm.set_sensitive(on)
            (self.warm.remove_css_class if on else self.warm.add_css_class)("off")
            self.cmd.send("night", NIGHT, "on" if on else "off")
        return False
