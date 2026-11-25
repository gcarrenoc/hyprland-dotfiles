"""Wi-Fi panel (under the bar's network icon).

  Wi-Fi on / off · the network in use (click: address, speed, Disconnect, Forget)
  Known networks  click to connect · Other networks  click, type the password
  Cable and VPN when there are any · Network settings… (nm-connection-editor)

Uses NetworkManager's own library, so a password never appears on a command line; NetworkManager
stores it (readable by root only). Networks with a user name (eduroam, WPA-Enterprise) that
aren't saved yet open the full settings. Scans only while open.
"""
import subprocess, time
import gi
from base import DropPanel, G, Gdk, GLib, Gtk, Pango, box, button, launch, fa, text
gi.require_version("NM", "1.0")
from gi.repository import NM

KM = NM.__getattr__("80211ApSecurityFlags")
AP_PRIVACY = NM.__getattr__("80211ApFlags").PRIVACY
PORTAL = "http://nmcheck.gnome.org/"


def signal_glyph(strength):
    return "wifi3" if strength >= 70 else "wifi2" if strength >= 45 else "wifi1" if strength >= 20 else "wifi0"


def security(ap):
    """open, psk, sae (WPA3 only), owe, 802.1x or wep — what is needed to join."""
    flags = int(ap.get_wpa_flags()) | int(ap.get_rsn_flags())
    if flags & int(KM.KEY_MGMT_PSK):
        return "psk"
    if flags & int(KM.KEY_MGMT_SAE):
        return "sae"
    if flags & (int(KM.KEY_MGMT_802_1X) | int(KM.KEY_MGMT_EAP_SUITE_B_192)):
        return "802.1x"
    if flags & int(KM.KEY_MGMT_OWE):
        return "owe"
    return "wep" if int(ap.get_flags()) & int(AP_PRIVACY) else "open"


def band(freq):
    return "2.4 GHz" if freq < 3000 else "5 GHz" if freq < 5925 else "6 GHz"


def new_profile(ssid, name, sec, password):
    """A NetworkManager profile for a network that isn't saved yet."""
    con = NM.SimpleConnection.new()
    s = NM.SettingConnection.new()
    s.set_property(NM.SETTING_CONNECTION_ID, name)
    s.set_property(NM.SETTING_CONNECTION_TYPE, NM.SETTING_WIRELESS_SETTING_NAME)
    s.set_property(NM.SETTING_CONNECTION_UUID, NM.utils_uuid_generate())
    con.add_setting(s)
    w = NM.SettingWireless.new()
    w.set_property(NM.SETTING_WIRELESS_SSID, GLib.Bytes.new(ssid))
    con.add_setting(w)
    if sec in ("psk", "sae", "owe"):
        k = NM.SettingWirelessSecurity.new()
        k.set_property(NM.SETTING_WIRELESS_SECURITY_KEY_MGMT, {"psk": "wpa-psk"}.get(sec, sec))
        if password:
            k.set_property(NM.SETTING_WIRELESS_SECURITY_PSK, password)
        con.add_setting(k)
    for ip in (NM.SettingIP4Config.new(), NM.SettingIP6Config.new()):
        ip.set_property(NM.SETTING_IP_CONFIG_METHOD, "auto")
        con.add_setting(ip)
    return con


class WifiPanel(DropPanel):
    def __init__(self, app):
        super().__init__(app, "wifi")
        self.nm = NM.Client.new(None)
        self.asking = None            # SSID whose password is being typed
        self.details = False          # the network in use, unfolded
        self.joining = None           # {ssid, name, new: profile we created or None, error}
        self.error = None             # (ssid, message)
        self.confirm = None           # SSID waiting for a second click on Forget
        self.shape, self.timer, self.ticks, self.hooked = None, 0, 0, None

    # ----- open / close
    def open(self):
        self.asking, self.details, self.error, self.confirm, self.shape = None, False, None, None, None
        self.scan()
        self.build()
        self.present()
        self.ticks = 0
        self.timer = GLib.timeout_add(1000, self.tick)

    def dismiss(self):
        super().dismiss()
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0
        self.asking = None
        self.clear()                                            # drop a half-typed password

    def tick(self):
        self.ticks += 1
        if self.ticks % 10 == 0:
            self.scan()
        self.build()
        return True

    def again(self, ms=150):
        GLib.timeout_add(ms, lambda: self.build() and False)

    # ----- reading
    def wifi(self):
        return next((d for d in self.nm.get_devices() if isinstance(d, NM.DeviceWifi)), None)

    def scan(self):
        dev = self.wifi()
        if dev and self.nm.wireless_get_enabled():
            dev.request_scan_async(None, self.ignore)

    @staticmethod
    def ignore(source, result):                                 # "scanned a moment ago" is fine
        try:
            source.request_scan_finish(result)
        except GLib.Error:
            pass

    def networks(self):
        """One entry per network name: the strongest access point, whether it's saved and in use."""
        dev = self.wifi()
        if not dev:
            return []
        active = dev.get_active_access_point()
        active_ssid = active.get_ssid().get_data() if active and active.get_ssid() else None
        profiles = {}                                           # saved ones, by network name
        for c in self.nm.get_connections():
            w = c.get_setting_wireless()
            if w and w.get_ssid() and w.get_mode() in (None, "infrastructure"):
                profiles.setdefault(w.get_ssid().get_data(), []).append(c)
        best = {}
        for ap in dev.get_access_points():
            raw = ap.get_ssid()
            ssid = raw.get_data() if raw else b""
            if not ssid or not ssid.strip(b"\0"):                # hidden
                continue
            if ssid not in best or ap.get_strength() > best[ssid].get_strength():
                best[ssid] = ap
        nets = []
        for ssid, ap in best.items():
            saved = sorted(profiles.get(ssid, []), key=lambda c: c.get_setting_connection().get_timestamp(), reverse=True)
            inuse = ssid == active_ssid and dev.get_state() == NM.DeviceState.ACTIVATED
            if inuse:
                ap = active
            nets.append({"ssid": ssid, "name": NM.utils_ssid_to_utf8(ssid), "ap": ap, "strength": ap.get_strength(),
                         "sec": security(ap), "saved": saved, "inuse": inuse})
        nets.sort(key=lambda n: (not n["inuse"], -(n["strength"] // 15), n["name"].lower()))
        return nets

    # ----- doing
    def finish(self, source, result, what):
        try:
            getattr(source, what)(result)
        except GLib.Error as e:
            self.error = (self.confirm or b"", e.message)
        self.again()

    def set_wifi(self, _switch, on):
        subprocess.Popen(["nmcli", "radio", "wifi", "on" if on else "off"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for ms in (400, 1200, 2500):
            GLib.timeout_add(ms, lambda: (self.scan(), self.build()) and False)
        return False

    def choose(self, n):
        self.error = self.confirm = None
        if n["inuse"]:
            self.details = not self.details
        elif n["saved"]:
            self.join(n, n["saved"][0])
        elif n["sec"] in ("802.1x", "wep"):                      # needs more than a password
            self.settings("--create", "--type=802-11-wireless")
            return
        elif n["sec"] in ("open", "owe"):
            self.join(n, None)
        else:
            self.asking = None if self.asking == n["ssid"] else n["ssid"]
        self.build(force=True)

    def join(self, n, profile, password=None):
        dev, ap = self.wifi(), n["ap"]
        job = self.joining = {"ssid": n["ssid"], "name": n["name"], "new": None, "ac": None, "done": False}
        self.asking = None
        if self.hooked:
            self.hooked[0].disconnect(self.hooked[1])
        self.hooked = (dev, dev.connect("state-changed", self.state_changed, job))
        def started(client, result, _=None):
            try:
                if profile:
                    job["ac"] = client.activate_connection_finish(result)
                else:
                    job["ac"] = client.add_and_activate_connection_finish(result)
                    job["new"] = job["ac"].get_connection()
            except GLib.Error as e:
                self.failed(job, e.message)
                return
            self.watch_active(job)
        if profile:
            self.nm.activate_connection_async(profile, dev, ap.get_path(), None, started)
        else:
            self.nm.add_and_activate_connection_async(new_profile(n["ssid"], n["name"], n["sec"], password),
                                                      dev, ap.get_path(), None, started)
        GLib.timeout_add_seconds(45, lambda: self.failed(job, "It took too long") and False)
        self.build(force=True)

    def watch_active(self, job):
        ac = job["ac"]
        def changed(*_):
            if job["done"]:
                return
            if ac.get_state() == NM.ActiveConnectionState.ACTIVATED:
                job["done"] = True
                if self.joining is job:
                    self.joining = None
                self.again(50)
            elif ac.get_state() == NM.ActiveConnectionState.DEACTIVATED:
                self.failed(job, "Couldn't connect")
        ac.connect("notify::state", changed)
        changed()

    def state_changed(self, _dev, new, _old, reason, job):
        # asked for the password a second time (with a reason) = the first one was wrong
        if job["done"] or new != int(NM.DeviceState.NEED_AUTH) or reason == int(NM.DeviceStateReason.NONE):
            return
        if job["new"] is not None:
            self.failed(job, "Wrong password")
        else:                                                   # saved: nm-applet asks for the new password
            job["done"] = True
            if self.joining is job:
                self.joining = None
            self.dismiss()

    def failed(self, job, message):
        if job["done"]:
            return
        job["done"] = True
        if job["new"] is not None:                              # don't keep a profile that never worked
            job["new"].delete_async(None, lambda c, r: self.finish(c, r, "delete_finish"))
        if self.joining is job:
            self.joining = None
            self.error = (job["ssid"], message)
            if job["new"] is not None and message == "Wrong password":
                self.asking = job["ssid"]
        if self.get_visible():
            self.build(force=True)

    def disconnect_wifi(self):
        ac = self.wifi().get_active_connection()
        self.details = False
        if ac:
            self.nm.deactivate_connection_async(ac, None, lambda c, r: self.finish(c, r, "deactivate_connection_finish"))
        self.again(400)

    def forget(self, n):
        if self.confirm != n["ssid"]:                            # second click does it
            self.confirm = n["ssid"]
            self.build(force=True)
            return
        self.confirm, self.details = None, False
        for c in n["saved"]:
            c.delete_async(None, lambda c, r: self.finish(c, r, "delete_finish"))
        self.again(400)

    def set_vpn(self, con, ac):
        if ac:
            self.nm.deactivate_connection_async(ac, None, lambda c, r: self.finish(c, r, "deactivate_connection_finish"))
        else:
            self.nm.activate_connection_async(con, None, None, None, lambda c, r: self.finish(c, r, "activate_connection_finish"))
        self.again(400)

    def settings(self, *args):
        self.dismiss()
        launch("nm-connection-editor", *args)

    def portal(self):
        self.dismiss()
        launch("xdg-open", PORTAL)

    # ----- contents
    def build(self, force=False):
        if not self.get_visible() and self.timer:
            return True
        on, dev = self.nm.wireless_get_enabled(), self.wifi()
        nets = self.networks() if on and dev else []
        wired = [d for d in self.nm.get_devices()
                 if isinstance(d, NM.DeviceEthernet) and d.get_state() == NM.DeviceState.ACTIVATED]
        acs = {ac.get_uuid(): ac for ac in self.nm.get_active_connections()}
        vpns = [(c, acs.get(c.get_uuid())) for c in self.nm.get_connections()
                if c.get_connection_type() in ("vpn", "wireguard")]
        portal = self.nm.get_connectivity() == NM.ConnectivityState.PORTAL
        shape = repr([on, [(n["ssid"], signal_glyph(n["strength"]), bool(n["saved"]), n["inuse"]) for n in nets],
                      self.asking, self.details, self.joining and self.joining["ssid"], self.error, self.confirm,
                      [d.get_iface() for d in wired], [(c.get_uuid(), ac and int(ac.get_state())) for c, ac in vpns], portal])
        if not force and (shape == self.shape or (self.asking and self.shape)):   # never rebuild under your typing
            return True
        self.shape = shape
        scroll = self.scroller.get_vadjustment().get_value() if getattr(self, "scroller", None) else 0
        self.clear()

        head = box(False, 8, css_classes=["card"])
        head.append(fa("wifi3" if on else "wifioff"))
        head.append(text("Wi-Fi", "title"))
        switch = Gtk.Switch(active=on, valign=Gtk.Align.CENTER, tooltip_text="Wi-Fi on / off")
        switch.connect("state-set", self.set_wifi)
        head.append(switch)
        self.panel.append(head)

        if portal:
            row = box(False, 8)
            row.append(fa("globe")); row.append(text("Log in to this network…"))
            self.panel.append(button(row, "Open the network's login page", self.portal, "row", "on"))
        for d in wired:
            card = self.section("CABLE")
            row = box(False, 8)
            row.append(fa("cable")); row.append(text("Connected")); row.append(text(self.address(d), "note", False))
            card.append(row)

        inuse = [n for n in nets if n["inuse"]]
        known = [n for n in nets if n["saved"] and not n["inuse"]]
        other = [n for n in nets if not n["saved"] and not n["inuse"]]
        lists = box(spacing=8)
        for title, group in (("CONNECTED", inuse), ("KNOWN NETWORKS", known), ("OTHER NETWORKS", other)):
            if group:
                part = box(spacing=8)
                part.append(text(title, "head"))
                card = box(spacing=2, css_classes=["card"])
                part.append(card)
                for n in group:
                    self.network(card, n)
                (self.panel if title == "CONNECTED" else lists).append(part)
        self.scroller = None
        if known or other:
            self.scroller = Gtk.ScrolledWindow(child=lists, hscrollbar_policy=Gtk.PolicyType.NEVER,
                                               propagate_natural_height=True, max_content_height=430)
            self.scroller.set_overflow(Gtk.Overflow.HIDDEN)          # round the cut-off edge too
            self.panel.append(self.scroller)
            if scroll:
                GLib.idle_add(lambda s=self.scroller: s.get_vadjustment().set_value(scroll) and False)
        elif on and dev and not inuse:
            self.panel.append(text("Looking for networks…", "note"))
        elif not dev:
            self.panel.append(text("No Wi-Fi adapter found", "note"))
        if self.error and self.error[0] not in [n["ssid"] for n in nets]:
            self.panel.append(text(self.error[1], "error"))

        if vpns:
            card = self.section("VPN")
            for c, ac in vpns:
                row = box(False, 8)
                row.append(fa("shield")); row.append(text(c.get_id()))
                if ac:
                    row.append(fa("check"))
                card.append(button(row, "Disconnect" if ac else "Connect", lambda c=c, ac=ac: self.set_vpn(c, ac),
                                   "row", *(["on"] if ac else [])))
        row = box(False, 8)
        row.append(fa("sliders")); row.append(text("Network settings…"))
        self.panel.append(button(row, "Saved networks, VPN, hidden networks…", self.settings, "row"))
        return True

    @staticmethod
    def address(dev):
        ip = dev.get_ip4_config()
        a = ip.get_addresses() if ip else []
        return a[0].get_address() if a else ""

    def network(self, card, n):
        joining = self.joining and self.joining["ssid"] == n["ssid"]
        row = box(False, 8)
        row.append(fa(signal_glyph(n["strength"])))
        row.append(text(n["name"]))
        if joining:
            row.append(Gtk.Spinner(spinning=True))
        elif n["inuse"]:
            row.append(fa("check"))
        elif n["sec"] not in ("open", "owe") and not n["saved"]:
            row.append(fa("lock"))
        tip = f"{n['strength']}%  ·  {band(n['ap'].get_frequency())}" + ("" if n["sec"] not in ("open", "owe") else "  ·  no password")
        card.append(button(row, tip, lambda: self.choose(n), "row", *(["on"] if n["inuse"] else [])))

        if self.error and self.error[0] == n["ssid"]:
            card.append(text(self.error[1], "error"))
        if self.asking == n["ssid"]:
            line = box(False, 6)
            entry = Gtk.PasswordEntry(show_peek_icon=True, hexpand=True, placeholder_text="Password")
            def go(*_):
                pw = entry.get_text()
                if n["sec"] == "psk" and not NM.utils_wpa_psk_valid(pw) or not pw:
                    entry.add_css_class("bad")
                    self.error = (n["ssid"], "The password has at least 8 characters")
                    self.build(force=True)
                    return
                self.error = None
                self.join(n, None, pw)
            entry.connect("activate", go)
            line.append(entry)
            line.append(button(Gtk.Label(label="Join"), "Connect", go, "action"))
            card.append(line)
            GLib.idle_add(lambda: entry.grab_focus() and False)
        if n["inuse"] and self.details:
            dev = self.wifi()
            speed = dev.get_bitrate() // 1000
            facts = [self.address(dev), band(n["ap"].get_frequency()), f"{speed} Mb/s" if speed else ""]
            card.append(text(" · ".join(f for f in facts if f), "note"))
            line = box(False, 6)
            line.append(button(Gtk.Label(label="Disconnect"), "Disconnect from this network", self.disconnect_wifi, "action"))
            if n["saved"]:
                sure = self.confirm == n["ssid"]
                line.append(button(Gtk.Label(label="Forget: click again" if sure else "Forget"),
                                   "Delete the saved password", lambda: self.forget(n), "action"))
            card.append(line)
