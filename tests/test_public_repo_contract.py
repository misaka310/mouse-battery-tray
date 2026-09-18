import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def test_readme_local_links_exist():
    text = README.read_text(encoding="utf-8")
    required_paths = [
        "docs/images/system-overview.svg",
        "docs/images/tray-states.svg",
        "docs/images/verification-pipeline.svg",
        "docs/architecture.md",
        "docs/protocol-notes.md",
        "docs/development.md",
        "docs/windows-gui-testing.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "THIRD_PARTY_NOTICES.md",
        "LICENSE",
    ]
    for relative in required_paths:
        assert relative in text
        assert (ROOT / relative).is_file(), relative


def test_readme_uses_generic_package_name():
    text = README.read_text(encoding="utf-8")
    assert "src/mouse_battery_tray/" in text
    assert "src/sprime_pm1_battery_tray/" not in text


def test_readme_svgs_are_well_formed():
    for name in ("system-overview.svg", "tray-states.svg", "verification-pipeline.svg"):
        ET.parse(ROOT / "docs" / "images" / name)
