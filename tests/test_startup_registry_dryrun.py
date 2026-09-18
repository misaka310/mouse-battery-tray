from sprime_pm1_battery_tray import startup


def test_set_startup_uses_run_key_without_shell_process(monkeypatch):
    written = []
    deleted = []
    cleaned = []

    class FakeKey:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(startup.winreg, "CreateKey", lambda *_args: FakeKey())
    monkeypatch.setattr(
        startup.winreg,
        "SetValueEx",
        lambda _key, name, _reserved, _kind, value: written.append((name, value)),
    )
    monkeypatch.setattr(startup, "_delete_run_value", lambda name: deleted.append(name))
    monkeypatch.setattr(
        startup,
        "_remove_legacy_startup_shortcuts",
        lambda: cleaned.append(True),
    )
    monkeypatch.setattr(startup, "_launch_command", lambda: '"C:\\Apps\\Mouse-Battery-Tray.exe"')

    startup.set_startup(True)

    assert written == [
        ("MouseBatteryTray", '"C:\\Apps\\Mouse-Battery-Tray.exe"')
    ]
    assert "SPRIME PM1 Battery Tray" in deleted
    assert cleaned == [True]


def test_disable_startup_removes_new_and_legacy_entries(monkeypatch):
    deleted = []
    monkeypatch.setattr(startup, "_delete_run_value", lambda name: deleted.append(name))
    monkeypatch.setattr(startup, "_remove_legacy_startup_shortcuts", lambda: None)

    startup.set_startup(False)

    assert deleted == ["MouseBatteryTray", "SPRIME PM1 Battery Tray"]


def test_launch_command_for_frozen_app_is_quoted(monkeypatch):
    monkeypatch.setattr(startup.sys, "frozen", True, raising=False)
    monkeypatch.setattr(startup.sys, "executable", r"C:\Program Files\Mouse Battery Tray\Mouse-Battery-Tray.exe")
    assert startup._launch_command() == (
        '"C:\\Program Files\\Mouse Battery Tray\\Mouse-Battery-Tray.exe"'
    )
