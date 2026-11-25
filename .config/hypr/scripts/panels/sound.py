"""Sound panel (under the bar's volume icon).

  Output        mute (click the icon), volume, and which speaker / headphones / screen to use
  Microphone    mute, level, which one to use, and which apps are listening
  Now playing   title, artist, previous / play / next (any MPRIS player: Spotify, Chrome…)
  Apps          the volume of each app that is playing
  Sound settings…   the full mixer (pavucontrol)

m = mute. Talks to PipeWire through pactl, and only while open. Volume stops at 100 %, like the keys.
"""
import json, re, subprocess, threading, time
from base import Commands, DropPanel, G, Gdk, GLib, Gtk, box, button, launch, fa, out, text

LISTENERS_IGNORED = {"PulseAudio Volume Control", "pavucontrol"}     # level meters, not recordings


# ---------- reading the sound system ----------
def pa(kind):
    try:
        return json.loads(out("pactl", "-f", "json", "list", kind) or "[]")
    except json.JSONDecodeError:
        return []


def percent(node):
    vols = [int(v["value_percent"].strip().rstrip("%")) for v in (node.get("volume") or {}).values()]
    return max(vols, default=0)


def device(node, default):
    """A sink / source as shown in the panel (None: nothing is plugged into it)."""
    port = next((p for p in node.get("ports") or [] if p["name"] == node.get("active_port")), {})
    if port.get("availability") == "not available" and node["name"] != default:
        return None
    props, desc = node.get("properties") or {}, node.get("description") or node["name"]
    bt = props.get("device.api") == "bluez5" or node["name"].startswith("bluez")
    name = desc if bt or not port.get("description") else port["description"]
    key = f"{name} {node['name']} {props.get('device.form_factor', '')}".lower()
    icon = ("bluetooth" if bt else "screen" if "hdmi" in key or "displayport" in key
            else "headphones" if "headphone" in key or "headset" in key
            else "usb" if props.get("device.bus") == "usb" else "speaker")
    if not bt and props.get("device.bus") == "usb":
        name = props.get("device.product.name") or desc
    return {"id": node["name"], "name": name, "icon": icon, "vol": percent(node),
            "mute": bool(node.get("mute")), "default": node["name"] == default}


def app_of(node):
    p = node.get("properties") or {}
    name = p.get("application.name") or p.get("application.process.binary") or p.get("node.name") or "App"
    media = p.get("media.name") or ""
    generic = media.lower() in ("", "playback", "audiostream", "audio stream", "audio-src", name.lower())
    return {"id": str(node["index"]), "name": name[:1].upper() + name[1:], "media": "" if generic else media,
            "icons": [x for x in (p.get("application.icon_name"), p.get("application.process.binary"),
                                  name.lower().replace(" ", "-"), name.lower()) if x],
            "vol": percent(node), "mute": bool(node.get("mute"))}


def players():
    sep = "\x1f"
    fmt = sep.join("{{%s}}" % f for f in ("playerInstance", "status", "title", "artist"))
    found = []
    for line in out("playerctl", "-a", "metadata", "--format", fmt).splitlines():
        f = line.split(sep)
        if len(f) == 4 and f[2].strip() and f[1] in ("Playing", "Paused"):
            found.append({"id": f[0], "playing": f[1] == "Playing", "title": f[2].strip(), "artist": f[3].strip()})
    found.sort(key=lambda p: not p["playing"])
    return found[:2]


def snapshot():
    try:
        info = json.loads(out("pactl", "-f", "json", "info") or "{}")
    except json.JSONDecodeError:
        info = {}
    sink, source = info.get("default_sink_name"), info.get("default_source_name")
    listening = {a["name"] for a in map(app_of, pa("source-outputs")) if a["name"] not in LISTENERS_IGNORED}
    return {
        "sinks": [d for d in (device(s, sink) for s in pa("sinks")) if d],
        "sources": [d for d in (device(s, source) for s in pa("sources") if not s["name"].endswith(".monitor")) if d],
        "apps": [app_of(s) for s in pa("sink-inputs")],
        "listening": sorted(listening),
        "pinned": re.findall(r"^\s+\d+\. Audio/(Sink|Source)\s+\S", out("wpctl", "status").partition("Default Configured")[2], re.M),
        "players": players(),
    }


def speaker_glyph(vol, mute):
    return G["muted"] if mute else G["vol0"] if vol == 0 else G["vol1"] if vol < 50 else G["vol2"]


class Level(Gtk.Box):
    """Mute button + slider + percentage for one thing (kind: sink, source, sink-input)."""
    def __init__(self, panel, kind, ident, what, glyph):
        super().__init__(spacing=6)
        self.panel, self.kind, self.ident, self.glyph = panel, kind, ident, glyph
        self.mute, self.touched = False, 0.0
        self.icon = Gtk.Label(css_classes=["icon"])
        self.btn = button(self.icon, f"Mute / unmute {what}", self.toggle)
        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        self.scale.set_draw_value(False); self.scale.set_hexpand(True)
        self.scale.set_tooltip_text(f"Volume of {what}" if kind != "source" else "Microphone level")
        self.scale.connect("change-value", self.moved)
        self.num = Gtk.Label(width_chars=4, xalign=1, css_classes=["value"])
        for w in (self.btn, self.scale, self.num):
            self.append(w)

    def paint(self, vol):
        self.icon.set_label(self.glyph(vol, self.mute))
        self.num.set_label(f"{vol}%")
        for w in (self.scale, self.btn):
            (w.add_css_class if self.mute else w.remove_css_class)("off")

    def show_state(self, vol, mute):
        if time.monotonic() - self.touched < 0.5:             # being dragged: don't fight the hand
            return
        self.mute = mute
        self.scale.set_value(min(vol, 100))
        self.paint(vol)

    def moved(self, _scale, _scroll, value):
        vol = max(0, min(100, round(value)))
        self.touched = time.monotonic()
        if self.mute and vol:
            self.mute = False
            self.panel.cmd.send(("mute", self.kind, self.ident), "pactl", f"set-{self.kind}-mute", self.ident, "0")
        self.panel.cmd.send(("vol", self.kind, self.ident), "pactl", f"set-{self.kind}-volume", self.ident, f"{vol}%")
        self.paint(vol)
        GLib.timeout_add(600, lambda: self.panel.refresh() and False)
        return False

    def toggle(self):
        self.mute = not self.mute
        self.touched = time.monotonic()
        self.panel.cmd.send(("mute", self.kind, self.ident), "pactl", f"set-{self.kind}-mute", self.ident,
                            "1" if self.mute else "0")
        self.paint(round(self.scale.get_value()))
        GLib.timeout_add(600, lambda: self.panel.refresh() and False)


# ---------- the panel ----------
class SoundPanel(DropPanel):
    def __init__(self, app):
        super().__init__(app, "sound")
        self.cmd = Commands()
        self.levels, self.shape = {}, None
        self.watcher, self.busy, self.again, self.timer = None, False, False, 0

    def key(self, c, val, code, mods):
        if val in (Gdk.KEY_m, Gdk.KEY_M) and "out" in self.levels:
            self.levels["out"].toggle()
            return True
        return super().key(c, val, code, mods)

    def open(self):
        self.build(snapshot())
        self.present()
        if "out" in self.levels:
            self.levels["out"].scale.grab_focus()
        self.watcher = subprocess.Popen(["pactl", "subscribe"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        threading.Thread(target=self.watch, args=(self.watcher,), daemon=True).start()
        self.timer = GLib.timeout_add(1500, self.refresh)                # Now playing has no pactl event

    def dismiss(self):
        super().dismiss()
        if self.watcher:
            self.watcher.terminate()
            threading.Thread(target=self.watcher.wait, daemon=True).start()
            self.watcher = None
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0

    # ----- keeping it up to date (only while open)
    def watch(self, proc):
        for line in proc.stdout:
            if re.search(r" on (sink|source|sink-input|source-output|server|card) ", line):
                GLib.idle_add(lambda: self.refresh() and False)

    def refresh(self):
        if not self.get_visible():
            return True
        if self.busy:                                         # one reading at a time; repeat once if more came in
            self.again = True
            return True
        self.busy, self.again = True, False
        def work():
            time.sleep(0.04)
            data = snapshot()
            GLib.idle_add(done, data)
        def done(data):
            self.busy = False
            if self.get_visible():
                self.build(data)
                if self.again:
                    self.refresh()
            return False
        threading.Thread(target=work, daemon=True).start()
        return True

    def run(self, *cmd):
        self.cmd.send(cmd, *cmd)
        GLib.timeout_add(250, lambda: self.refresh() and False)

    # ----- contents
    def build(self, d):
        shape = json.dumps([[(x["id"], x["name"], x["default"]) for x in d["sinks"]],
                            [(x["id"], x["name"], x["default"]) for x in d["sources"]],
                            [(x["id"], x["name"], x["media"]) for x in d["apps"]], d["listening"], d["players"], d["pinned"]])
        if shape != self.shape:
            self.shape = shape
            focus = next((k for k, l in self.levels.items() if l.scale.is_focus()), None)
            old = self.levels
            self.levels = {}
            self.clear()
            self.fill(d)
            for k, l in self.levels.items():                    # a rebuild must not undo a drag
                if k in old and old[k].ident == l.ident and time.monotonic() - old[k].touched < 0.5:
                    l.touched, l.mute = old[k].touched, old[k].mute
                    l.scale.set_value(old[k].scale.get_value()); l.paint(round(old[k].scale.get_value()))
            if focus in self.levels:
                self.levels[focus].scale.grab_focus()
        for key, items in (("out", d["sinks"]), ("mic", d["sources"])):
            cur = next((x for x in items if x["default"]), None)
            if cur and key in self.levels:
                self.levels[key].show_state(cur["vol"], cur["mute"])
        for a in d["apps"]:
            if "app" + a["id"] in self.levels:
                self.levels["app" + a["id"]].show_state(a["vol"], a["mute"])

    def devices(self, card, kind, items, pinned=False):
        if len(items) < 2:                                      # a single one: just say which
            for x in items:
                card.append(text(x["name"], "note"))
        for x in items if len(items) > 1 else []:
            row = box(False, 8)
            row.append(fa(x["icon"] if kind == "sink" or x["icon"] != "speaker" else "mic"))
            row.append(text(x["name"]))
            if x["default"]:
                row.append(fa("check"))
            card.append(button(row, x["name"], lambda i=x["id"]: self.run("pactl", f"set-default-{kind}", i),
                               "device", *(["on"] if x["default"] else [])))
        if pinned:                                              # you chose one: it stays, even if headphones come
            row = box(False, 8)
            row.append(fa("auto")); row.append(text("Choose automatically"))
            card.append(button(row, "Follow what is plugged in (headphones take over)",
                               lambda: self.run("wpctl", "clear-default", "0" if kind == "sink" else "1"), "device"))

    def fill(self, d):
        cur = next((x for x in d["sinks"] if x["default"]), None)
        card = self.section("OUTPUT")
        if cur:
            self.levels["out"] = Level(self, "sink", cur["id"], "the output", speaker_glyph)
            card.append(self.levels["out"])
            self.devices(card, "sink", d["sinks"], "Sink" in d["pinned"])
        else:
            card.append(text("No output found", "note"))

        cur = next((x for x in d["sources"] if x["default"]), None)
        if cur:
            card = self.section("MICROPHONE")
            self.levels["mic"] = Level(self, "source", cur["id"], "the microphone",
                                       lambda v, m: G["micoff"] if m else G["mic"])
            card.append(self.levels["mic"])
            self.devices(card, "source", d["sources"], "Source" in d["pinned"])
            if d["listening"]:
                card.append(text("In use by " + ", ".join(d["listening"]), "note"))

        if d["players"]:
            card = self.section("NOW PLAYING")
            for p in d["players"]:
                row, names = box(False, 2), box(spacing=0, hexpand=True)
                names.append(text(p["title"], "title"))
                if p["artist"]:
                    names.append(text(p["artist"], "note"))
                names.set_tooltip_text(" — ".join(x for x in (p["title"], p["artist"]) if x))
                row.append(names)
                for glyph, tip, action in (("prev", "Previous", "previous"),
                                           ("pause" if p["playing"] else "play", "Play / pause", "play-pause"),
                                           ("next", "Next", "next")):
                    row.append(button(fa(glyph), tip, lambda i=p["id"], a=action: self.run("playerctl", "-p", i, a)))
                card.append(row)

        if d["apps"]:
            card = self.section("APPS")
            rows = box(spacing=4)
            theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
            for a in d["apps"]:
                head = box(False, 8)
                icon = next((i for i in a["icons"] if theme.has_icon(i)), "audio-x-generic")
                head.append(Gtk.Image(icon_name=icon, pixel_size=18, margin_start=8))
                head.append(text(a["name"] + (f"  ·  {a['media']}" if a["media"] else "")))
                rows.append(head)
                level = self.levels["app" + a["id"]] = Level(self, "sink-input", a["id"], a["name"], speaker_glyph)
                rows.append(level)
            card.append(Gtk.ScrolledWindow(child=rows, hscrollbar_policy=Gtk.PolicyType.NEVER,
                                           propagate_natural_height=True, max_content_height=250))

        row = box(False, 8)
        row.append(fa("sliders"))
        row.append(text("Sound settings…"))
        self.panel.append(button(row, "Open the full mixer (pavucontrol)", self.mixer, "device"))

    def mixer(self):
        self.dismiss()
        launch("pavucontrol")
