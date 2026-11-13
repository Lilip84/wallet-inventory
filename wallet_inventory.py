#!/usr/bin/env python3
"""wallet-inventory - detect crypto wallet software installed on a local machine.

Scans Chrome-family browser profiles (Chrome, Chromium, Edge, Brave, Vivaldi, Opera)
and known desktop wallet directories. Reports only non-sensitive metadata:
wallet name, version, browser, profile, install date.

Never reads keys, seed phrases, cookies, history or any wallet data.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

__version__ = "0.1.0"

# Extensions whose manifest name does not contain an obvious wallet keyword.
KNOWN_EXTENSIONS = {
    "nkbihfbeogaeaoehlefnkodbefgpgknn": "MetaMask",
    "bfnaelmomeimhlpmgjnjophhpkkoljpa": "Phantom",
    "acmacodkjbdgmoleebolmdjonilkdbch": "Rabby",
    "ibnejdfjmmkpcnlpebklmnkoeoihofec": "TronLink",
    "dmkamcknogkgcdfhhbddcghachkejeap": "Keplr",
    "eigdlffakeeklglpkneghbbeokmovedgp": "Binance Wallet",
}

WALLET_KEYWORDS = (
    "wallet", "metamask", "phantom", "rabby", "keplr", "tronlink",
    "coinbase", "trust wallet", "ledger", "trezor", "exodus", "backpack",
    "solflare", "slope", "martian", "petra", "sui wallet", "tonkeeper",
)

CHROME_FAMILY = {
    "Chrome": ("google-chrome", ".config/google-chrome"),
    "Chromium": ("chromium", ".config/chromium"),
    "Edge": ("microsoft-edge", ".config/microsoft-edge"),
    "Brave": ("BraveSoftware/Brave-Browser", ".config/BraveSoftware/Brave-Browser"),
    "Vivaldi": ("vivaldi", ".config/vivaldi"),
    "Opera": ("opera", ".config/opera"),
}

DESKTOP_WALLETS = {
    "Electrum": "~/.electrum",
    "Exodus": "~/.config/Exodus",
    "Atomic Wallet": "~/.config/atomic",
    "Coinomi": "~/.config/Coinomi",
    "Monero GUI": "~/.bitmonero",
    "Bitcoin Core": "~/.bitcoin",
}


@dataclass
class Found:
    wallet: str
    version: str
    browser: str
    profile: str
    installed: str | None
    path: str
    source: str


def _iso(ts: float | None) -> str | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def _read_manifest(ext_dir: Path) -> dict | None:
    manifest = ext_dir / "manifest.json"
    if not manifest.is_file():
        return None
    try:
        with manifest.open(encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _classify(ext_id: str, name: str) -> str | None:
    if ext_id in KNOWN_EXTENSIONS:
        return KNOWN_EXTENSIONS[ext_id]
    lowered = name.lower()
    for keyword in WALLET_KEYWORDS:
        if keyword in lowered:
            return name.strip() or ext_id
    return None


def chrome_profiles(root: Path) -> Iterator[Path]:
    """Yield every directory that holds an Extensions subfolder."""
    if not root.is_dir():
        return
    candidates = [root]
    try:
        candidates += [p for p in root.iterdir() if p.is_dir()]
    except OSError:
        return
    for profile in candidates:
        if (profile / "Extensions").is_dir():
            yield profile


def scan_browsers(home: Path) -> list[Found]:
    found: list[Found] = []
    for browser, (_, rel) in CHROME_FAMILY.items():
        root = home / rel
        for profile in chrome_profiles(root):
            ext_root = profile / "Extensions"
            try:
                ext_dirs = [p for p in ext_root.iterdir() if p.is_dir()]
            except OSError:
                continue
            for ext in ext_dirs:
                versions = sorted([p for p in ext.iterdir() if p.is_dir()], reverse=True)
                if not versions:
                    continue
                version_dir = versions[0]
                manifest = _read_manifest(version_dir)
                if manifest is None:
                    continue
                wallet = _classify(ext.name, str(manifest.get("name", "")))
                if wallet is None:
                    continue
                try:
                    installed = _iso(version_dir.stat().st_ctime)
                except OSError:
                    installed = None
                found.append(Found(
                    wallet=wallet,
                    version=str(manifest.get("version", "")),
                    browser=browser,
                    profile=profile.name,
                    installed=installed,
                    path=str(ext),
                    source="extension",
                ))
    return found


def scan_desktop(home: Path) -> list[Found]:
    found: list[Found] = []
    for wallet, rel in DESKTOP_WALLETS.items():
        path = Path(os.path.expanduser(rel))
        if path.is_dir():
            try:
                installed = _iso(path.stat().st_ctime)
            except OSError:
                installed = None
            found.append(Found(
                wallet=wallet,
                version="",
                browser="-",
                profile="-",
                installed=installed,
                path=str(path),
                source="desktop",
            ))
    return found


def collect(home: Path | None = None) -> list[Found]:
    home = home or Path.home()
    rows = scan_browsers(home) + scan_desktop(home)
    rows.sort(key=lambda r: (r.wallet.lower(), r.browser.lower(), r.profile.lower()))
    return rows


def render_table(rows: Iterable[Found]) -> str:
    rows = list(rows)
    if not rows:
        return "Wallets not found."
    headers = ("WALLET", "VERSION", "BROWSER", "PROFILE", "INSTALLED")
    data = [(r.wallet, r.version or "-", r.browser, r.profile, r.installed or "?") for r in rows]
    widths = [max(len(h), *(len(row[i]) for row in data)) for i, h in enumerate(headers)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    out = [line, "-" * len(line)]
    for row in data:
        out.append("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wallet-inventory",
        description="List crypto wallet software installed on this machine (metadata only).",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--home", default=None, help="override home directory (testing)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    rows = collect(Path(args.home).expanduser() if args.home else None)
    if args.json:
        print(json.dumps({
            "host": platform.node() or "unknown",
            "os": f"{platform.system()} {platform.release()}",
            "count": len(rows),
            "wallets": [asdict(r) for r in rows],
        }, ensure_ascii=False, indent=2))
    else:
        print(render_table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
