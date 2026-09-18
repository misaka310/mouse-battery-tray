# Architecture

## Goals

Mouse Battery Trayは、機種ごとに異なるHID取得方法を利用者向けUIから切り離し、同じtray UXへ統合することを目的とします。

主な設計目標:

- device固有のUSB/HID処理をadapter単位に閉じ込める
- UIは共通のbattery stateだけを扱う
- sleep / disconnectedとtransport errorを区別する
- pollingとmanual refreshの同時HID accessを避ける
- Windows user権限だけでstartup設定できる
- packaged EXEでも同じ検証契約を維持する

## Component map

```text
mouse_battery_tray
├── attack_shark.py
│   └── Beken-family passive packet reader
├── hid_protocol.py
│   └── SPRIME PM1 Feature Report reader
├── battery_reader.py
│   └── adapter selection + normalized result
├── app.py
│   ├── polling worker
│   ├── main-thread queue
│   ├── low-battery notification
│   └── tray lifecycle
├── icon_renderer.py
│   └── 32x32 state icon
├── settings_window.py
│   └── status + settings UI
├── startup.py
│   └── HKCU Run registration
└── single_instance.py
    └── Windows named mutex
```

## Normalized state

各adapterは最終的に、UIが解釈できる同じ形へ変換します。

```python
{
    "status": "connected",
    "device": "ATTACK SHARK X1",
    "battery": 90,
    "charging": False,
    "full": False,
}
```

UI側はVID/PIDやreport layoutを知りません。これにより新しいprotocolを追加しても、tray rendering、通知、settings UIを変更せずに済む構成です。

## Adapter selection

`battery_reader.get_battery_info()` は、対応adapterを決められた順序で問い合わせます。

1. ATTACK SHARK/Beken receiverを列挙
2. 見つからなければSPRIME PM1を列挙
3. 対応機種がなければ `device_not_found`

将来的にadapter数が増える場合はregistry化できますが、現在は2系統なので単純な明示順序を選んでいます。不要な抽象化を避け、device supportの責任範囲を読みやすく保つためです。

## Concurrency model

GUI main loopとHID I/Oを同じthreadで実行すると、receiver待ちでUIが止まります。そのため:

- Tk / Settings更新: main thread
- periodic HID polling: daemon worker
- tray icon loop: background thread
- worker → UI: `queue.Queue`
- HID poll: `threading.Lock` でsingle-flight

manual refreshは別workerを起動しますが、poll lockを取得できなければ追加HID accessを行いません。これにより定期更新と連打されたmanual refreshがreceiverを同時に開かないようにしています。

## Error semantics

| Internal state | Tray | Meaning |
|---|---|---|
| `connected` | percentage / `99+` | battery value available |
| `disconnected` | `--` | receiver exists but mouse may be sleeping/offline |
| `device_not_found` | `--` | supported receiver is not present |
| `permission_or_access_error` | `!` | endpoint could not be opened |
| `read_failed` / `protocol_unknown` | `!` | transport or protocol failed |

「値がまだ来ない」と「通信処理が壊れた」を同じ表示にしないことをUX上の要件にしています。

## Windows integration

### Start with Windows

`startup.py` は `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` のみを使用します。

- administrator/UAC不要
- current userだけに適用
- 旧 `SPRIME PM1 Battery Tray` entryをmigration時に除去

### Single instance

named mutex `Local\Mouse_Battery_Tray_SingleInstance` を作成し、2個目の起動を終了させます。startup + manual launchが重なってもtray iconが重複しません。

## Packaging boundary

PyInstallerの生成物はone-folder構成です。`--smoke-test` はpackageされたEXE自身で次を確認します。

- required imports
- config load
- icon rendering
- real HID read
- Settings UI initialization

source treeで通るだけではなく、package後にhidden importやDLLが欠けていないことまで確認するためです。

## Network / privacy boundary

通常のbattery monitoringはネットワーク通信を必要としません。HID device、config、logsはlocal Windows user session内で扱います。

CIやsource取得を除き、runtimeがremote APIへbattery情報やdevice identifierを送信する処理はありません。

## Adding another mouse family

新しいprotocolを追加する場合は、既存UIを変更するのではなくadapterを追加します。

1. receiver VID/PIDとendpointを実機で記録
2. raw report parserを純粋関数として実装
3. error classificationを共通statusへ変換
4. `battery_reader.py` にadapter selectionを追加
5. raw packet fixtureでunit test
6. 実機probe
7. packaged EXE smoke

対応機種をREADMEへ「verified」と書くのは手順6まで通した機種だけです。
