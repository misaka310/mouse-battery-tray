# Public Release Checklist

## 1. 実機動作

少なくとも1台の対応マウスを2.4GHzレシーバーで接続して確認します。

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe scripts\check_real_device.py
```

確認すること:

- `pytest tests/` が通る
- HID読み取り結果が `connected`
- X1実機ではモデル名が `ATTACK SHARK X1` と判別される
- EXEが `dist\Mouse-Battery-Tray` に生成される
- 生成EXEの `--smoke-test` が通る

## 2. 手動UX確認

- タスクトレイに残量数字が出る
- 100%は `99+`
- スリープまたは切断中は `--`
- HID通信エラーは `!`
- `Refresh now` が使える
- `Show settings` が開く
- `Start on boot` がHKCU Runへ反映される
- 二重起動してもプロセスは1個
- `Quit` で常駐プロセスが終了する

## 3. 互換性表記

READMEに確認済みモデル、接続方式、VID/PID、未確認範囲を明記します。VID/PIDが一致しても、ファームウェアやパケット形式が異なる個体まで対応済みとは扱いません。

## 4. Gitに含めないもの

- `.venv/`
- `dist/`
- `build/`
- `*.spec`
- `*.log`
- ローカル設定
- HID調査時の個人環境ログ

## 5. 最小リリース条件

- READMEだけで用途・対応モデル・制約が分かる
- 対応実機でHID読み取り済み
- EXEビルドとスモークが通る
- 通常ユーザーがWindows検索から起動できる
- 自動起動と二重起動防止が機能する
