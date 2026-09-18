from mouse_battery_tray.app import build_arg_parser


def test_show_settings_cli_flag():
    args = build_arg_parser().parse_args(["--show-settings"])

    assert args.show_settings is True
    assert args.smoke_test is False


def test_default_cli_flags_are_disabled():
    args = build_arg_parser().parse_args([])

    assert args.show_settings is False
    assert args.smoke_test is False
