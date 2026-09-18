import importlib
import os
from pathlib import Path


def test_log_directory_is_stable_across_working_directories(tmp_path):
    first_cwd = tmp_path / "first"
    second_cwd = tmp_path / "second"
    first_cwd.mkdir()
    second_cwd.mkdir()

    from mouse_battery_tray import config

    config = importlib.reload(config)
    expected = (Path(config.__file__).resolve().parents[2] / "logs").resolve()

    original_cwd = Path.cwd()
    try:
        os.chdir(first_cwd)
        first = Path(config.get_log_dir()).resolve()
        os.chdir(second_cwd)
        second = Path(config.get_log_dir()).resolve()
    finally:
        os.chdir(original_cwd)

    assert first == expected
    assert second == expected
    assert first.is_absolute()
