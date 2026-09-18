from contextlib import contextmanager

from sprime_pm1_battery_tray import startup


def _fake_registry(monkeypatch):
    values = {}

    @contextmanager
    def create_key(_root, _path):
        yield object()

    @contextmanager
    def open_key(_root, _path, _reserved=0, _access=0):
        yield object()

    def set_value(_key, name, _reserved, _kind, value):
        values[name] = value

    def query_value(_key, name):
        if name not in values:
            raise FileNotFoundError(name)
        return values[name], startup.winreg.REG_SZ

    def delete_value(_key, name):
        if name not in values:
            raise FileNotFoundError(name)
        del values[name]

    monkeypatch.setattr(startup.winreg, "CreateKey", create_key)
    monkeypatch.setattr(startup.winreg, "OpenKey", open_key)
    monkeypatch.setattr(startup.winreg, "SetValueEx", set_value)
    monkeypatch.setattr(startup.winreg, "QueryValueEx", query_value)
    monkeypatch.setattr(startup.winreg, "DeleteValue", delete_value)
    return values


def test_startup_registry_toggle(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    values = _fake_registry(monkeypatch)
    monkeypatch.setattr(startup, "_launch_command", lambda: '"C:\\Mouse Battery Tray\\Mouse-Battery-Tray.exe"')

    assert not startup.is_startup_enabled()

    startup.set_startup(True)
    assert startup.is_startup_enabled()
    assert startup.APP_NAME in values

    startup.set_startup(False)
    assert not startup.is_startup_enabled()


def test_launch_command_quotes_frozen_executable(monkeypatch):
    monkeypatch.setattr(startup.sys, "frozen", True, raising=False)
    monkeypatch.setattr(startup.sys, "executable", r"C:\Program Files\Mouse Battery Tray\Mouse-Battery-Tray.exe")

    assert startup._launch_command() == '"C:\\Program Files\\Mouse Battery Tray\\Mouse-Battery-Tray.exe"'
