from __future__ import annotations

import time

import tray_uia_smoke as smoke


def find_tray_button():
    def predicate(text: str) -> bool:
        return text.casefold().startswith(smoke.APP_NAME.casefold())

    def find_or_refresh_overflow():
        button = smoke.find_button(smoke.candidate_scopes(), predicate)
        if button is not None:
            return button
        smoke.open_hidden_icons_if_needed()
        time.sleep(0.4)
        return smoke.find_button(smoke.candidate_scopes(), predicate)

    return smoke.wait_until(
        "Mouse Battery Tray tray icon",
        find_or_refresh_overflow,
        timeout=20,
        interval=0.8,
    )


def main() -> int:
    smoke.find_tray_button = find_tray_button
    return smoke.main()


if __name__ == "__main__":
    raise SystemExit(main())
