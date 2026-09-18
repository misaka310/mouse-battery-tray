# 開発・検証ガイド

## セットアップ

```powershell
.\scripts\setup.ps1
```

## ソースから実行

```powershell
.\run.ps1
```

## 品質確認

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest tests
```

PM1のFeature Report実装に加え、ATTACK SHARK系の受信パケット解析もユニットテストします。X1では実機確認済みの `03 B1 40 01 <battery>` パケットを回帰テストに固定しています。

## EXEビルド

```powershell
.\scripts\build.ps1
```

生成物:

```text
dist/Mouse-Battery-Tray/Mouse-Battery-Tray.exe
```

## ユーザー環境へのインストール

```powershell
.\scripts\install_user.ps1 [-EnableStartup]
```

`%LOCALAPPDATA%\Programs\Mouse Battery Tray` に配置し、Windows検索用のスタートメニューショートカットを作成します。旧SPRIME PM1版の設定が存在する場合は互換設定として移行します。

## 実機確認

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe scripts\check_real_device.py
```

対応マウスが見つかり、バッテリーを取得できれば `connected` で終了します。実機HID確認はGitHub Actionsでは代替できません。

## 実機E2E

```powershell
.\scripts\e2e.ps1
```

ユニットテスト、HID実機読み取り、EXEビルド、EXEスモークをまとめて確認します。ATTACK SHARK X1またはSPRIME PM1など、このリポジトリが対応する実機が必要です。

## 公開前確認

1. ユニットテストとRuffが通る
2. 対応マウス接続状態で `scripts\check_real_device.py` が `connected`
3. `dist\Mouse-Battery-Tray\Mouse-Battery-Tray.exe --smoke-test` が通る
4. 通知領域に残量、`--`、`!` が表示される
5. 二重起動しても常駐プロセスが1個だけ
6. Windowsログイン時の自動起動が有効ならHKCU Runから起動する
7. READMEの実機確認範囲を誇張しない
8. `dist/`、`.venv/`、ログ、ローカル設定をGitへ含めない

詳細は [公開前チェックリスト](public-release-checklist.md) を参照してください。

## 技術スタック

- GUI: CustomTkinter、Pystray、Pillow
- HID: hidapi
- アイコン描画: Arial Bold
