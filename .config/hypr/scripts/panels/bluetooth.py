"""Bluetooth panel (under the bar's Bluetooth icon).

  Bluetooth on / off · My devices (click: connect; … : disconnect, forget; battery when known)
  Nearby devices (click to pair: codes are shown and confirmed here) · Bluetooth settings… (blueman)

Talks to BlueZ over D-Bus. Looks for devices only while open. Pairing started here is answered here
and only for that device; requests coming from other devices go to blueman-applet as before.
"""
import subprocess
from base import DropPanel, G, Gio, GLib, Gtk, box, button, launch, fa, text

DEV, ADAPTER, BATTERY, PROPS = "org.bluez.Device1", "org.bluez.Adapter1", "org.bluez.Battery1", "org.freedesktop.DBus.Properties"
AGENT_PATH = "/local/BarPanels/agent"
AGENT_XML = """<node><interface name="org.bluez.Agent1">
  <method name="Release"/><method name="Cancel"/>
  <method name="RequestPinCode"><arg type="o" direction="in"/><arg type="s" direction="out"/></method>
  <method name="DisplayPinCode"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
  <method name="RequestPasskey"><arg type="o" direction="in"/><arg type="u" direction="out"/></method>
  <method name="DisplayPasskey"><arg type="o" direction="in"/><arg type="u" direction="in"/><arg type="q" direction="in"/></method>
  <method name="RequestConfirmation"><arg type="o" direction="in"/><arg type="u" direction="in"/></method>
  <method name="RequestAuthorization"><arg type="o" direction="in"/></method>
  <method name="AuthorizeService"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
</interface></node>"""
ICONS = {"audio-headset": "headphones", "audio-headphones": "headphones", "audio-card": "loudspeaker", "input-keyboard": "keyboard",
         "input-mouse": "mouse", "input-tablet": "mouse", "input-gaming": "gamepad", "phone": "phone", "computer": "speaker",
         "printer": "printer", "video-display": "screen", "watch": "watch"}
ERRORS = {"AuthenticationFailed": "Pairing failed: wrong or missing code", "AuthenticationTimeout": "No answer from the device",
          "AuthenticationCanceled": "Pairing cancelled", "AuthenticationRejected": "The device refused to pair",
          "ConnectionAttemptFailed": "Couldn't reach it: is it on and in pairing mode?"}


def prop(proxy, name, default=None):
    v = proxy.get_cached_property(name) if proxy else None
    return default if v is None else v.unpack()


class BluetoothPanel(DropPanel):
    def __init__(self, app):
        super().__init__(app, "bluetooth")
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.objects = Gio.DBusObjectManagerClient.new_for_bus_sync(
            Gio.BusType.SYSTEM, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START, "org.bluez", "/", None, None, None)
        self.objects.connect("object-added", self.changed)
        self.objects.connect("object-removed", self.changed)
        self.objects.connect("interface-added", self.changed)
        self.objects.connect("interface-removed", self.changed)
        self.objects.connect("interface-proxy-properties-changed", self.changed)
        self.shape, self.queued, self.scanning = None, False, False
        self.busy = {}                # device path → what is happening ("Connecting…")
        self.errors = {}              # device path (or "") → message
        self.unfolded = self.confirm = None
        self.pairing = None           # device path being paired from here
        self.prompt = None            # {kind, text, call}: a question from the device
        self.agent = 0

    # ----- open / close
    def open(self):
        self.shape, self.unfolded, self.confirm, self.errors = None, None, None, {}
        self.build()
        self.present()
        self.scan(True)

    def dismiss(self):
        super().dismiss()
        self.scan(False)
        self.answer(False)

    def changed(self, *_):
        if self.get_visible() and not self.queued:              # many changes at once while scanning: one rebuild
            self.queued = True
            def later():
                self.queued = False
                if self.get_visible():
                    self.build()
                return False
            GLib.timeout_add(150, later)

    # ----- BlueZ
    def adapter(self):
        found = [o.get_interface(ADAPTER) for o in self.objects.get_objects() if o.get_interface(ADAPTER)]
        return found[0] if found else None

    def devices(self):
        res = []
        for o in self.objects.get_objects():
            d = o.get_interface(DEV)
            if not d:
                continue
            paired, name = prop(d, "Paired", False), prop(d, "Name")
            if not paired and (not name or prop(d, "RSSI") is None):   # unnamed, or not in range now
                continue
            res.append({"path": o.get_object_path(), "proxy": d, "name": prop(d, "Alias") or name or "Device",
                        "icon": ICONS.get(prop(d, "Icon", ""), "bluetooth"), "paired": paired,
                        "connected": prop(d, "Connected", False), "rssi": prop(d, "RSSI", -100),
                        "battery": prop(o.get_interface(BATTERY), "Percentage")})
        res.sort(key=lambda d: (not d["connected"], d["name"].lower()))
        return res

    def call(self, proxy, method, args, done=None, timeout=30000):
        def finish(p, result):
            err = None
            try:
                p.call_finish(result)
            except GLib.Error as e:
                err = Gio.DBusError.get_remote_error(e) or "error"
                err = (err.rsplit(".", 1)[-1], e.message.split(": ", 1)[-1])
            if done:
                done(err)
        proxy.call(method, args, Gio.DBusCallFlags.NONE, timeout, None, finish)

    def put(self, proxy, iface, name, value, done=None):
        self.call(proxy, PROPS + ".Set", GLib.Variant("(ssv)", (iface, name, value)), done)

    def scan(self, on):
        a = self.adapter()
        if not a or on == self.scanning or (on and (not prop(a, "Powered") or self.busy)):
            return
        self.scanning = on
        self.call(a, "StartDiscovery" if on else "StopDiscovery", None,
                  lambda err: err and on and setattr(self, "scanning", False))

    def set_power(self, _switch, on):
        a = self.adapter()
        if on:
            subprocess.run(["rfkill", "unblock", "bluetooth"], capture_output=True, timeout=3)
        else:
            self.scanning = False
        def done(err):
            self.errors = {"": "Couldn't switch Bluetooth " + ("on" if on else "off")} if err else {}
            self.shape = None
            self.changed()
            if on and not err:
                GLib.timeout_add(600, lambda: self.get_visible() and self.scan(True) and False)
        if a:
            GLib.timeout_add(300 if on else 0, lambda: self.put(a, ADAPTER, "Powered", GLib.Variant("b", on), done) and False)
        return False

    def choose(self, d):
        self.confirm = None
        self.errors.pop(d["path"], None)
        if d["path"] in self.busy:
            return
        if not d["paired"]:
            self.pair(d)
        elif d["connected"]:
            self.unfold(d)
            return
        else:
            self.connect_device(d["path"], d["proxy"])
        self.build()

    def unfold(self, d):
        self.confirm = None
        self.unfolded = None if self.unfolded == d["path"] else d["path"]
        self.build()

    def start(self, path, what):
        self.scan(False)                                        # scanning makes connecting slow
        self.busy[path] = what

    def end(self, path, err=None, fallback=""):
        self.busy.pop(path, None)
        if err:
            self.errors[path] = ERRORS.get(err[0], fallback)
        if self.get_visible():
            self.scan(True)
            self.build()

    def connect_device(self, path, proxy):
        self.start(path, "Connecting…")
        self.call(proxy, "Connect", None, lambda err: self.end(path, err, "Couldn't connect: is it on and nearby?"))

    def disconnect_device(self, d):
        self.unfolded = None
        self.start(d["path"], "Disconnecting…")
        self.call(d["proxy"], "Disconnect", None, lambda err: self.end(d["path"], err, "Couldn't disconnect"))
        self.build()

    def forget(self, d):
        if self.confirm != d["path"]:                           # second click does it
            self.confirm = d["path"]
            self.build()
            return
        self.confirm = self.unfolded = None
        self.call(self.adapter(), "RemoveDevice", GLib.Variant("(o)", (d["path"],)), lambda err: self.changed())

    # ----- pairing
    def pair(self, d):
        if self.pairing:
            return
        path, proxy = d["path"], d["proxy"]
        self.pairing = path
        self.start(path, "Pairing…")
        def paired(err):
            self.answer(False)
            self.pairing = None
            self.unregister()
            if err and err[0] != "AlreadyExists":
                self.end(path, err, "Couldn't pair: is it in pairing mode?")
                return
            self.put(proxy, DEV, "Trusted", GLib.Variant("b", True))     # reconnects by itself from now on
            self.busy.pop(path, None)
            self.connect_device(path, proxy)
            self.build()
        def registered(err):
            if err and err[0] != "AlreadyExists":
                self.pairing = None
                self.end(path, err, "Couldn't start pairing")
                return
            self.call(proxy, "Pair", None, paired, 90000)
        if not self.agent:
            info = Gio.DBusNodeInfo.new_for_xml(AGENT_XML).interfaces[0]
            self.agent = self.bus.register_object(AGENT_PATH, info, self.asked, None, None)
        self.manager("RegisterAgent", GLib.Variant("(os)", (AGENT_PATH, "KeyboardDisplay")), registered)

    def manager(self, method, args, done=None):
        def finish(bus, result):
            err = None
            try:
                bus.call_finish(result)
            except GLib.Error as e:
                err = ((Gio.DBusError.get_remote_error(e) or "error").rsplit(".", 1)[-1], e.message)
            if done:
                done(err)
        self.bus.call("org.bluez", "/org/bluez", "org.bluez.AgentManager1", method, args, None,
                      Gio.DBusCallFlags.NONE, 10000, None, finish)

    def unregister(self):
        self.manager("UnregisterAgent", GLib.Variant("(o)", (AGENT_PATH,)))
        if self.agent:
            self.bus.unregister_object(self.agent)
            self.agent = 0

    def asked(self, _bus, _sender, _path, _iface, method, params, call):
        """BlueZ asks something about a pairing."""
        args = params.unpack()
        if method in ("Release", "Cancel"):
            self.prompt = None
            call.return_value(None)
            self.changed()
            return
        if args[0] != self.pairing or not self.get_visible():    # only the device you chose, with you looking
            call.return_dbus_error("org.bluez.Error.Rejected", "Not expected")
            return
        if method in ("RequestAuthorization", "AuthorizeService"):
            call.return_value(None)
            return
        self.answer(False)
        if method == "DisplayPinCode":
            self.prompt = {"kind": "show", "text": f"Type {args[1]} on the device, then Enter", "call": None}
            call.return_value(None)
        elif method == "DisplayPasskey":
            self.prompt = {"kind": "show", "text": f"Type {args[1]:06d} on the device, then Enter", "call": None}
            call.return_value(None)
        elif method == "RequestConfirmation":
            self.prompt = {"kind": "confirm", "text": f"Does it show {args[1]:06d}?", "call": call}
        elif method == "RequestPinCode":
            self.prompt = {"kind": "pin", "text": "Code of the device (often 0000)", "call": call}
        else:                                                    # RequestPasskey
            self.prompt = {"kind": "passkey", "text": "Number shown by the device", "call": call}
        self.build()

    def answer(self, value):
        """value: False = no, True = yes, or the typed code."""
        p, self.prompt = self.prompt, None
        if not p or not p["call"]:
            return
        if value is False:
            p["call"].return_dbus_error("org.bluez.Error.Rejected", "Rejected")
        elif p["kind"] == "confirm":
            p["call"].return_value(None)
        elif p["kind"] == "pin":
            p["call"].return_value(GLib.Variant("(s)", (value[:16],)))
        elif value.isdigit() and int(value) <= 999999:
            p["call"].return_value(GLib.Variant("(u)", (int(value),)))
        else:
            p["call"].return_dbus_error("org.bluez.Error.Rejected", "Not a number")

    def reply(self, value):
        self.answer(value)
        self.build()

    def settings(self):
        self.dismiss()
        launch("blueman-manager")

    # ----- contents
    def build(self):
        a = self.adapter()
        on = bool(a and prop(a, "Powered", False))
        devs = self.devices() if on else []
        shape = repr((bool(a), on, [(d["path"], d["name"], d["icon"], d["paired"], d["connected"], d["battery"]) for d in devs],
                      self.busy, self.errors, self.unfolded, self.confirm, self.prompt and self.prompt["text"]))
        if shape == self.shape:
            return
        self.shape = shape
        scroll = self.scroller.get_vadjustment().get_value() if getattr(self, "scroller", None) else 0
        typing = self.prompt and self.prompt["kind"] in ("pin", "passkey") and getattr(self, "entry", None)
        typed = self.entry.get_text() if typing else ""
        self.clear()
        self.entry = self.scroller = None

        head = box(False, 8, css_classes=["card"])
        head.append(fa("bluetooth" if on else "btoff"))
        head.append(text("Bluetooth", "title"))
        if a:
            switch = Gtk.Switch(active=on, valign=Gtk.Align.CENTER, tooltip_text="Bluetooth on / off")
            switch.connect("state-set", self.set_power)
            head.append(switch)
        self.panel.append(head)
        if not a:
            self.panel.append(text("No Bluetooth adapter found", "note"))
        if "" in self.errors:
            self.panel.append(text(self.errors[""], "error"))

        mine, near = [d for d in devs if d["paired"]], [d for d in devs if not d["paired"]]
        if mine:
            card = self.section("MY DEVICES")
            for d in mine:
                self.device(card, d, typed)
        if on:
            part = box(spacing=8)
            part.append(text("NEARBY DEVICES", "head"))
            card = box(spacing=2, css_classes=["card"])
            part.append(card)
            for d in near:
                self.device(card, d, typed)
            if not near:
                row = box(False, 8)
                row.append(Gtk.Spinner(spinning=True)); row.append(text("Looking… (put it in pairing mode)", "note"))
                card.append(row)
            self.scroller = Gtk.ScrolledWindow(child=part, hscrollbar_policy=Gtk.PolicyType.NEVER,
                                               propagate_natural_height=True, max_content_height=330)
            self.scroller.set_overflow(Gtk.Overflow.HIDDEN)
            self.panel.append(self.scroller)
            if scroll:
                GLib.idle_add(lambda s=self.scroller: s.get_vadjustment().set_value(scroll) and False)
        row = box(False, 8)
        row.append(fa("sliders")); row.append(text("Bluetooth settings…"))
        self.panel.append(button(row, "Open blueman", self.settings, "row"))

    def device(self, card, d, typed):
        path, row = d["path"], box(False, 8)
        row.append(fa(d["icon"]))
        row.append(text(d["name"]))
        if d["battery"] is not None:
            row.append(text(f"{d['battery']}%", "note", False))
        if path in self.busy:
            row.append(Gtk.Spinner(spinning=True))
        elif d["connected"]:
            row.append(fa("check"))
        tip = "Connected" if d["connected"] else "Connect" if d["paired"] else "Pair"
        main = button(row, tip, lambda: self.choose(d), "row", *(["on"] if d["connected"] else []))
        main.set_hexpand(True)
        line = box(False, 2)
        line.append(main)
        if d["paired"]:
            line.append(button(fa("more"), "Disconnect, forget", lambda: self.unfold(d)))
        card.append(line)
        if path in self.busy and not (self.prompt and path == self.pairing):
            card.append(text(self.busy[path], "note"))
        if path in self.errors:
            card.append(text(self.errors[path], "error"))
        if self.prompt and path == self.pairing:
            self.question(card, typed)
        if self.unfolded == path:
            line = box(False, 6)
            if d["connected"]:
                line.append(button(Gtk.Label(label="Disconnect"), "Disconnect", lambda: self.disconnect_device(d), "action"))
            sure = self.confirm == path
            line.append(button(Gtk.Label(label="Forget: click again" if sure else "Forget"), "Remove this device",
                               lambda: self.forget(d), "action"))
            card.append(line)

    def question(self, card, typed):
        p = self.prompt
        label = Gtk.Label(label=p["text"], xalign=0, wrap=True, css_classes=["title"])
        card.append(label)
        line = box(False, 6)
        if p["kind"] == "confirm":
            line.append(button(Gtk.Label(label="Yes, pair"), "The codes match", lambda: self.reply(True), "action"))
            line.append(button(Gtk.Label(label="No"), "The codes are different", lambda: self.reply(False), "action"))
        elif p["kind"] in ("pin", "passkey"):
            self.entry = Gtk.Entry(hexpand=True, text=typed, max_length=16)
            self.entry.connect("activate", lambda e: e.get_text() and self.reply(e.get_text()))
            line.append(self.entry)
            line.append(button(Gtk.Label(label="OK"), "Send the code", lambda e=self.entry: e.get_text() and self.reply(e.get_text()), "action"))
            GLib.idle_add(lambda e=self.entry: e.grab_focus() and False)
        card.append(line)
