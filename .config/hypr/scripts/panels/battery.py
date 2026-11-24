"""Battery panel (under the bar's battery).

  Charge, time left and what the battery is doing · power mode (power saver, balanced, performance)
  Details: power in use, health and cycles, charge limit

Power modes: power-profiles-daemon over D-Bus, so a change made elsewhere (Spotlight, power-watch at
20 %) shows at once. Charge: UPower. Read only while open.
"""
from pathlib import Path
from base import DropPanel, G, Gio, GLib, Gtk, box, button, lucide, text

BAT = Path("/sys/class/power_supply/BAT0")
SAVER_STATE = Path.home() / ".cache/power-watch-saver"        # power-watch switched to power saver by itself
MODES = (("power-saver", "Power saver", "leaf"), ("balanced", "Balanced", "scale"), ("performance", "Performance", "rocket"))
LIMITED = {"lap-detected": "Limited: the laptop is on your lap", "high-operating-temperature": "Limited: the laptop is hot"}
CHARGING, DISCHARGING, EMPTY, FULL, WAITING = 1, 2, 3, 4, 5    # UPower states


def number(name):
    try:
        return int((BAT / name).read_text())
    except (OSError, ValueError):
        return None


def duration(seconds):
    m = round(seconds / 60)
    return f"{m // 60} h {m % 60:02d} min" if m >= 60 else f"{m} min"


class BatteryPanel(DropPanel):
    def __init__(self, app):
        super().__init__(app, "battery")
        def proxy(name, path, iface):
            return Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SYSTEM, Gio.DBusProxyFlags.NONE, None, name, path, iface, None)
        self.bat = proxy("org.freedesktop.UPower", "/org/freedesktop/UPower/devices/battery_BAT0", "org.freedesktop.UPower.Device")
        self.power = proxy("net.hadess.PowerProfiles", "/net/hadess/PowerProfiles", "net.hadess.PowerProfiles")
        for p in (self.bat, self.power):
            p.connect("g-properties-changed", lambda *_: self.get_visible() and self.build())
        self.shape, self.timer, self.error = None, 0, None

    def open(self):
        self.error, self.shape = None, None
        self.build()
        self.present()
        self.timer = GLib.timeout_add_seconds(2, lambda: self.build() or True)

    def dismiss(self):
        super().dismiss()
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0

    @staticmethod
    def get(proxy, name, default=None):
        v = proxy.get_cached_property(name)
        return default if v is None else v.unpack()

    def set_mode(self, mode):
        def done(proxy, result):
            try:
                proxy.call_finish(result)
                self.error = None
            except GLib.Error as e:
                self.error = e.message
            self.build()
        self.power.call("org.freedesktop.DBus.Properties.Set",
                        GLib.Variant("(ssv)", ("net.hadess.PowerProfiles", "ActiveProfile", GLib.Variant("s", mode))),
                        Gio.DBusCallFlags.NONE, 5000, None, done)

    def status(self):
        """(glyph, percent, what the battery is doing)"""
        pct, state = round(self.get(self.bat, "Percentage", 0)), self.get(self.bat, "State", 0)
        limit = number("charge_control_end_threshold")
        if state == CHARGING:
            # UPower's estimate is to 100 %: with a charge limit it would be too long
            left = self.get(self.bat, "TimeToFull", 0)
            full, now, rate = number("energy_full"), number("energy_now"), number("power_now")
            goal = limit if limit and limit < 100 and pct < limit else 100
            if goal < 100 and full and now and rate:
                left = max(0, full * goal / 100 - now) / rate * 3600
            return "charging", pct, "Charging" + (f" · {duration(left)} to {goal}%" if left >= 60 else "")
        if state == DISCHARGING:
            left = self.get(self.bat, "TimeToEmpty", 0)
            glyph = "battery" if pct < 15 else "low" if pct < 40 else "medium" if pct < 75 else "full"
            return glyph, pct, "On battery" + (f" · {duration(left)} left" if left >= 60 else "")
        if state == FULL or pct >= 99:
            return "plug", pct, "Full"
        return "plug", pct, "Plugged in" + (f" · resting at the {limit}% limit" if limit and limit < 100 else " · not charging")

    def build(self):
        glyph, pct, doing = self.status()
        mode, degraded = self.get(self.power, "ActiveProfile"), self.get(self.power, "PerformanceDegraded", "")
        modes = [p.get("Profile") for p in self.get(self.power, "Profiles", [])]
        automatic = mode == "power-saver" and SAVER_STATE.exists()
        facts = []
        watts = (number("power_now") or 0) / 1e6
        if watts >= 0.1:
            facts.append(("Charging with" if glyph == "charging" else "Using", f"{watts:.1f} W"))
        full, design, cycles = number("energy_full"), number("energy_full_design"), number("cycle_count")
        if full and design:
            facts.append(("Battery health", f"{min(100, round(full / design * 100))}%" + (f" · {cycles} cycles" if cycles else "")))
        start, end = number("charge_control_start_threshold"), number("charge_control_end_threshold")
        if end and end < 100:
            facts.append(("Charge limit", f"{end}%" + (f" (from {start}%)" if start else "")))
        shape = repr((glyph, pct, doing, mode, degraded, modes, automatic, facts, self.error))
        if shape == self.shape:
            return
        self.shape = shape
        focused = self.get_focus()
        keep = focused.get_name() if focused else None
        self.clear()

        card = box(spacing=6, css_classes=["card"])
        row = box(False, 8)
        row.append(lucide(glyph)); row.append(text("Battery", "title")); row.append(text(f"{pct}%", "title", False))
        card.append(row)
        bar = Gtk.ProgressBar(fraction=pct / 100)
        bar.add_css_class("low" if glyph in ("battery", "low") and pct <= 20 else "level")
        card.append(bar)
        card.append(text(doing, "note"))
        self.panel.append(card)

        card = self.section("POWER MODE")
        for key, name, icon in MODES:
            if key not in modes:
                continue
            row = box(False, 8)
            row.append(lucide(icon)); row.append(text(name))
            if key == mode:
                row.append(lucide("check"))
            b = button(row, name, lambda k=key: self.set_mode(k), "row", *(["on"] if key == mode else []))
            b.set_name(key)
            card.append(b)
            if keep == key:
                b.grab_focus()
        if not modes:
            card.append(text("power-profiles-daemon isn't running", "note"))
        if automatic:
            card.append(text("Set at 20%; your mode returns on the charger", "note"))
        if mode == "performance" and degraded:
            card.append(text(LIMITED.get(degraded, f"Limited: {degraded}"), "note"))
        if self.error:
            card.append(text(self.error, "error"))

        if facts:
            card = self.section("DETAILS")
            for name, value in facts:
                row = box(False, 8)
                row.append(text(name)); row.append(text(value, "note", False))
                card.append(row)
