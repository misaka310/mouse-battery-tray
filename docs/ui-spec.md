# UI仕様: Mouse Battery Tray

## 目的

Windowsの通知領域で、対応ワイヤレスマウスのバッテリー残量を設定アプリを開かず確認できるようにする。

## 表示方針

Windows通知領域では長い固定文字列ではなく、32×32の数字アイコンを使う。

- 0〜99%: 数字
- 100%: `99+`
- 未接続・スリープ・まだ通知待ち: `--`
- HID通信エラー: `!`
- ホバー: 自動判別したデバイス名と残量を表示
- 充電中: 緑系背景
- 低残量: 赤系背景

## 設定画面

`Show settings` から以下を確認・変更できる。

- 自動判別したデバイス名
- バッテリー残量
- 接続状態
- 最終更新時刻
- 最終エラー
- Refresh interval
- Low battery threshold
- Low battery notification
- Start on boot
- Refresh Now
- Open Logs

## トレイメニュー

- Refresh now
- Show settings
- Start on boot
- Open logs
- Quit

## 完了条件

- 対応マウスを自動判別する
- ATTACK SHARK X1では2.4GHzレシーバーから実残量を読める
- SPRIME PM1の既存Feature Report読み取りを壊さない
- 二重起動しない
- Windowsログイン時に自動起動できる
- 通常利用者がWindows検索から `Mouse Battery Tray` を起動できる
