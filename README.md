# Mouse Battery Tray

Windowsの通知領域に、対応ワイヤレスマウスのバッテリー残量を大きな数字で常駐表示する軽量ツールです。設定画面を開かなくても、残量・充電中・未接続・通信エラーを確認できます。

このリポジトリは従来の **SPRIME PM1 Battery Tray** を後方互換のまま汎用化したものです。内部Pythonパッケージ名には互換性のため旧名 `sprime_pm1_battery_tray` を当面残します。

> **非公式・非提携について**
> このプロジェクトは独立して開発された非公式ツールです。SPRIME、ATTACK SHARKその他のメーカーの公式製品、提携製品、承認製品、スポンサー製品ではありません。製品名・サービス名・商標は各権利者に帰属します。

## 目的とHappy Path

通常利用者は `Mouse-Battery-Tray.exe` を起動するだけです。

1. 対応マウスを2.4GHzレシーバーで接続する。
2. `Mouse-Battery-Tray.exe` を起動する。
3. アプリが対応デバイスを自動検出する。
4. 通知領域のアイコンにバッテリー残量が表示される。
5. 必要なら右クリック → `Show settings` で、優先するマウス・更新間隔・低残量通知・自動起動を変更する。

通常利用ではターミナル、PowerShell、VBS、管理者権限を要求しません。

## 表示

| 表示 | 状態 |
|---|---|
| `96` | 接続中・残量96% |
| `99+` | 100%または満充電に近い状態 |
| `--` | 未接続、スリープ中、またはバッテリー値待ち |
| `!` | HID通信エラー |

通常は黒〜濃いグレー、充電中は緑、低残量時は赤い背景で表示します。

## 対応デバイス

### SPRIME PM1

- 2.4GHz USBレシーバー
- VID `0x1915` / PID `0xAC1C`
- Feature Report `0x05`
- 既存実装で実機確認済み

### ATTACK SHARK X1

- 2.4GHz USBレシーバー: VID `0x1D57` / PID `0xFA60`
- 有線時: VID `0x1D57` / PID `0x2111`
- 2.4GHz時のバッテリーパケットは `[0x03, device_id, 0x40, subtype, battery, ...]` 形式
- `0xFA60` は他のBeken系ATTACK SHARK機でも使われるため、無線時の表示名は誤判定を避けてX1系として扱う
- バッテリー取得方式は MIT License の [incconutwo/mouse-battery-tray](https://github.com/incconutwo/mouse-battery-tray) の公開実装およびX1実機報告を参考にしている

## 複数マウスの扱い

設定 `preferred_device` は次の値を取ります。

- `auto` — 読み取り可能な対応マウスを自動選択（既定）
- `attack_shark_x1` — ATTACK SHARK X1系を優先
- `sprime_pm1` — SPRIME PM1を優先

Autoでは、接続中で有効なバッテリー値を返したデバイスを優先します。複数の対応マウスが同時に存在する場合でも、1つのトレイアイコンには1台分だけを表示します。

## 必須の完了条件

次をすべて満たした状態だけを完成扱いにします。

- PM1の既存バッテリー読み取りが回帰しない
- X1の2.4GHzバッテリーパケットを読み取れる
- 自動検出と優先デバイス選択が動く
- トレイ表示が `0-99` / `99+` / `--` / `!` を正しく使い分ける
- 低残量通知と手動更新が選択中デバイス名を使う
- 自動起動はユーザー権限のWindows Runキーで行い、隠しPowerShell/VBSを起動しない
- 単体テスト、Windowsビルド、GUI smoke が通る
- 実機X1で公式ATTACK SHARKソフトと同じ残量が確認できる

## 設定と移行

従来の `%APPDATA%\SprimePM1BatteryTray\config.json` は読み込み対象として残し、新しい設定は `%APPDATA%\MouseBatteryTray\config.json` に保存します。既存設定は初回起動時に安全に引き継ぎます。

旧SPRIME PM1版の自動起動エントリ／ショートカットが残っている場合は、新しい `MouseBatteryTray` の自動起動設定へ移行し、二重起動しないよう整理します。

## 開発・検証

実装は既存のPM1実装を保持しつつ、デバイス固有HID処理をアダプタ境界へ分離します。X1のBeken系パケット処理には上記MIT OSSの知見を利用し、コピーした実装・派生部分はライセンス表示を保持します。

公開前にはユニットテスト、Windows EXEビルド、GUI smoke、実機HID確認を行います。

## ライセンス

このリポジトリのコードは [MIT License](LICENSE) で公開しています。第三者実装を利用した箇所は `THIRD_PARTY_NOTICES.md` に記載します。
