import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wallet_inventory import collect, render_table


def make_extension(home: Path, browser_dir: str, profile: str, ext_id: str,
                   name: str, version: str = "1.0.0") -> None:
    version_dir = home / browser_dir / profile / "Extensions" / ext_id / version
    version_dir.mkdir(parents=True)
    (version_dir / "manifest.json").write_text(
        json.dumps({"name": name, "version": version}), encoding="utf-8"
    )


class WalletInventoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(self.id().replace(".", "_"))
        self.home = Path.cwd() / self.tmp
        self.home.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.home, ignore_errors=True)

    def test_detects_known_extension_by_id(self) -> None:
        make_extension(self.home, ".config/google-chrome", "Default",
                       "nkbihfbeogaeaoehlefnkodbefgpgknn", "MetaMask", "11.2.0")
        rows = collect(self.home)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].wallet, "MetaMask")
        self.assertEqual(rows[0].version, "11.2.0")
        self.assertEqual(rows[0].browser, "Chrome")
        self.assertEqual(rows[0].profile, "Default")

    def test_detects_unknown_extension_by_keyword(self) -> None:
        make_extension(self.home, ".config/BraveSoftware/Brave-Browser", "Profile 1",
                       "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "Some Wallet Beta")
        rows = collect(self.home)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].browser, "Brave")
        self.assertIn("Wallet", rows[0].wallet)

    def test_ignores_non_wallet_extensions(self) -> None:
        make_extension(self.home, ".config/chromium", "Default",
                       "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "Adblock Plus")
        self.assertEqual(collect(self.home), [])

    def test_ignores_broken_manifest(self) -> None:
        version_dir = self.home / ".config/chromium/Default/Extensions/cccc/1.0"
        version_dir.mkdir(parents=True)
        (version_dir / "manifest.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(collect(self.home), [])

    def test_multiple_profiles_and_versions(self) -> None:
        make_extension(self.home, ".config/google-chrome", "Default",
                       "nkbihfbeogaeaoehlefnkodbefgpgknn", "MetaMask", "11.0.0")
        make_extension(self.home, ".config/google-chrome", "Profile 2",
                       "bfnaelmomeimhlpmgjnjophhpkkoljpa", "Phantom", "24.1.0")
        rows = collect(self.home)
        self.assertEqual({r.wallet for r in rows}, {"MetaMask", "Phantom"})

    def test_empty_machine(self) -> None:
        self.assertEqual(collect(self.home), [])
        self.assertEqual(render_table([]), "Wallets not found.")


if __name__ == "__main__":
    unittest.main()
