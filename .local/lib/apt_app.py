"""apt_app — keep an app from a vendor's signed apt repository up to date in the home folder.

Used by ~/.local/bin/claude-desktop-update and vscode-update. No password; silent while all is well.

The app lives in <opt>/<version>/, with `current` pointing at the one in use. A new version is
unpacked next to it and used from the app's next start (its launcher), or at once if it isn't open.

Every download is verified before it's used:
  1. the saved key has the pinned fingerprint (and is the only one in the file)
  2. the repository index (InRelease) is signed by that key — checksums are read only from the
     verified text
  3. the package list matches the signed SHA-256
  4. the .deb matches the package list's SHA-256
Temporary keyrings only: your GPG keyring is never touched.

Exit 75 = no connection / server down: the service tries again by itself (Restart=on-failure).
Exit 1  = something is wrong (signature, checksum, package): one notification a day.
No successful check for 10 days also notifies, so updates can't stop without you knowing.
"""
import fcntl, hashlib, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request
from pathlib import Path

ARCH = "amd64"
KEEP = 2                                                   # versions kept on disk (current + previous)
STALE_DAYS = 10
TRY_AGAIN = 75


class Wrong(Exception):
    """Not a connection problem: needs attention."""


def say(msg):
    print(f"→ {msg}", flush=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def newer(a, b):            # pacman's version comparison: is a newer than b?
    return subprocess.run(["vercmp", a, b], capture_output=True, text=True).stdout.strip() == "1"


class AptApp:
    def __init__(self, title, package, repo, fingerprint, key, opt, binary, lib, integrate=None):
        self.title, self.package, self.repo, self.fingerprint = title, package, repo, fingerprint
        self.key, self.opt, self.binary, self.lib, self.integrate = Path(key), Path(opt), binary, lib, integrate

    # ----- what is on disk
    def installed(self):
        try:
            return (self.opt / "current" / "VERSION").read_text().strip()
        except OSError:
            return None

    def link(self, name):
        p = self.opt / name
        return os.readlink(p).split("/")[-1] if p.is_symlink() else None

    def running(self):
        return subprocess.run(["pgrep", "-f", f"^{self.opt}/[^ ]*/{self.binary}( |$)"], capture_output=True).returncode == 0

    def point(self, name, version):
        tmp = self.opt / (name + ".new")
        tmp.unlink(missing_ok=True)
        tmp.symlink_to(version)
        tmp.replace(self.opt / name)

    def switch_if_idle(self):
        """Use the newest unpacked version now, unless the app is open (then: at its next start)."""
        nxt = self.link("next")
        if not nxt or self.running():
            return False
        self.point("current", nxt)
        (self.opt / "next").unlink()
        return True

    def prune(self):
        """Drop old versions, never the one in use or the one waiting; not while the app is open."""
        if self.running():
            return
        keep = {self.link("current"), self.link("next")} - {None}
        others = [p for p in self.opt.iterdir() if p.is_dir() and not p.is_symlink()
                  and (p / "VERSION").exists() and p.name not in keep]
        others.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for old in others[max(0, KEEP - len(keep)):]:
            shutil.rmtree(old, ignore_errors=True)

    # ----- download and verify
    def fetch(self, url, dest):
        req = urllib.request.Request(url, headers={"User-Agent": "apt-app"})
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)

    def newest(self, work):
        """The newest package in the verified index: its fields."""
        gnupg = work / "gnupg"
        gnupg.mkdir(mode=0o700)
        if not self.key.exists():
            raise Wrong(f"missing key {self.key}")
        shown = subprocess.run(["gpg", "--homedir", str(gnupg), "--show-keys", "--with-colons", str(self.key)],
                               capture_output=True, text=True).stdout
        if len(re.findall(r"^pub:", shown, re.M)) != 1 \
                or re.findall(r"^fpr:+([0-9A-F]{40}):", shown, re.M)[:1] != [self.fingerprint]:
            raise Wrong(f"the saved key is not the pinned one ({self.fingerprint})")
        keyring = work / "key.gpg"
        keyring.write_bytes(subprocess.run(["gpg", "--homedir", str(gnupg), "--dearmor"],
                                           input=self.key.read_bytes(), capture_output=True, check=True).stdout)
        self.fetch(f"{self.repo}/dists/stable/InRelease", work / "InRelease")
        verified = work / "Release.verified"
        r = subprocess.run(["gpgv", "--keyring", str(keyring), "--output", str(verified), str(work / "InRelease")],
                           capture_output=True, text=True)
        if r.returncode != 0 or not verified.exists():
            raise Wrong("the repository's signature is NOT valid (or its key changed):\n" + r.stderr)
        m = re.search(rf"^ ([0-9a-f]{{64}}) +\d+ main/binary-{ARCH}/Packages$", verified.read_text(), re.M)
        if not m:
            raise Wrong("no checksum for the package list in the signed index")
        self.fetch(f"{self.repo}/dists/stable/main/binary-{ARCH}/Packages", work / "Packages")
        if sha256(work / "Packages") != m.group(1):
            raise Wrong("the package list does not match the signed checksum")
        say("signature and checksums OK")
        found = [dict(re.findall(r"^([A-Za-z0-9-]+): (.*)$", b, re.M))
                 for b in (work / "Packages").read_text().strip().split("\n\n")]
        found = [e for e in found if e.get("Package") == self.package and e.get("Architecture") == ARCH
                 and re.fullmatch(r"[0-9][0-9A-Za-z.+~-]*", e.get("Version", ""))]
        if not found:
            raise Wrong("the package isn't in the repository")
        best = found[0]
        for e in found[1:]:
            if newer(e["Version"], best["Version"]):
                best = e
        return best

    def unpack(self, work, best):
        version, deb = best["Version"], work / "app.deb"
        self.fetch(f"{self.repo}/{best['Filename']}", deb)
        if sha256(deb) != best["SHA256"]:
            raise Wrong("the .deb does not match the package list's checksum")
        say(".deb checksum OK — unpacking")
        stage, root = work / "deb", work / "root"
        stage.mkdir(); root.mkdir()
        subprocess.run(["bsdtar", "-xf", str(deb), "-C", str(stage)], check=True)
        subprocess.run(["bsdtar", "-xf", str(next(stage.glob("data.tar.*"))), "-C", str(root)], check=True)
        app = root / self.lib
        (app / "chrome-sandbox").chmod(0o755)                # no setuid: Arch's user-namespace sandbox works
        (app / "VERSION").write_text(version + "\n")
        if self.integrate:
            self.integrate(app, root)
        dest = self.opt / version
        shutil.rmtree(dest, ignore_errors=True)              # a leftover; never in use (checked in update)
        app.rename(dest)                                    # same filesystem: all or nothing
        self.point("next", version)

    def update(self, check_only=False):
        self.opt.mkdir(parents=True, exist_ok=True)
        lock = open(self.opt / ".lock", "w")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            say("another update is running")
            return
        if not check_only:
            if self.switch_if_idle():
                say(f"now using {self.installed()} (unpacked earlier)")
            self.prune()
        for left in self.opt.glob(".update-*"):              # from a run that was cut off
            shutil.rmtree(left, ignore_errors=True)
        work = Path(tempfile.mkdtemp(prefix=".update-", dir=self.opt))
        try:
            best = self.newest(work)
            have, pending, version = self.installed(), self.link("next"), best["Version"]
            (self.opt / ".checked").touch()
            if (have and not newer(version, have)) or pending == version:
                say(f"up to date: {have}" + (f" ({pending} ready for the next start)" if pending else ""))
                return
            say(f"new version: {version}" + (f" (in use: {have})" if have else ""))
            if check_only:
                return
            self.unpack(work, best)
            if self.switch_if_idle():
                say(f"{self.title} {version} installed and in use")
                self.prune()
            else:
                say(f"{self.title} {version} ready — used from its next start")
        finally:
            shutil.rmtree(work, ignore_errors=True)

    # ----- telling you, only when it matters
    def warn(self, text):
        stamp = self.opt / ".warned"
        if stamp.exists() and time.time() - stamp.stat().st_mtime < 86400:
            return
        stamp.touch()
        subprocess.run(["notify-send", "-a", "Updates", "-i", "dialog-warning", f"{self.title} isn't being updated", text],
                       capture_output=True)

    def main(self):
        try:
            self.update("--check" in sys.argv)
            (self.opt / ".warned").unlink(missing_ok=True)
            return 0
        except Wrong as e:
            print(f"✗ {e}", file=sys.stderr)
            self.warn(str(e).splitlines()[0])
            return 1
        except urllib.error.HTTPError as e:
            print(f"✗ server answered {e.code}", file=sys.stderr)
            code = TRY_AGAIN if e.code >= 500 or e.code == 429 else 1
            if code == 1:
                self.warn(f"The download server answered {e.code}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            print(f"✗ no connection: {e}", file=sys.stderr)
            code = TRY_AGAIN
        except (OSError, subprocess.CalledProcessError, StopIteration) as e:
            print(f"✗ {e}", file=sys.stderr)
            self.warn(str(e)[:120])
            code = 1
        checked = self.opt / ".checked"
        if code == TRY_AGAIN and checked.exists() and time.time() - checked.stat().st_mtime > STALE_DAYS * 86400:
            self.warn(f"No successful check for {STALE_DAYS} days")
        return code
