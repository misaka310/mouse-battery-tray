# HID protocol notes

この文書は、対応機種について**実機で確認した事実**と、外部実装から参照した情報を分けて残すための記録です。

## ATTACK SHARK X1

### Receiver identity

2026-09-18に2.4 GHz receiver接続で確認:

| Field | Value |
|---|---|
| VID | `0x1D57` |
| PID | `0xFA60` |
| battery interface | `2` |
| usage page | `0x0A` |
| observed device id | `0xB1` |

Bluetooth pathは確認対象外です。

### Observed packet

実機で受信したbattery packet:

```text
03 B1 40 01 5A
```

現在のparserでは次のように扱います。

| Offset | Observed value | Interpretation |
|---|---|---|
| 0 | `0x03` | report prefix |
| 1 | `0xB1` | X1 device id |
| 2 | `0x40` | battery report type |
| 3 | `0x01` | subtype/status |
| 4 | `0x5A` | battery percentage = 90 |

`0xB1` のX1 mappingと `0x5A = 90` はこの実機で確認しています。

### Passive-report behavior

X1側はPM1のようにbattery queryを送るのではなく、receiver endpointから届くbattery heartbeatを短時間待ちます。

receiverはWindowsから見えていてもmouseがsleepしているとpacketが来ない場合があるため、timeoutはtransport errorではなく `disconnected / --` として扱います。

### Upstream reference

Beken-family packet形式と他モデルのdevice id mappingは、MIT Licenseの [incconutwo/mouse-battery-tray](https://github.com/incconutwo/mouse-battery-tray) を参照しました。

本プロジェクト独自のX1実機確認範囲は:

- `VID 0x1D57 / PID 0xFA60`
- interface 2 / usage page `0x0A`
- device id `0xB1`
- raw battery packetの受信
- packaged EXEからの90%取得

他のATTACK SHARKモデル名はcompatible mappingとして保持していますが、本READMEのsupported tableでは実機確認したX1だけをverified扱いにしています。

## SPRIME PM1

### Receiver identity

| Field | Value |
|---|---|
| VID | `0x1915` |
| PID | `0xAC1C` |
| Feature Report ID | `0x05` |
| query command | `0x15` |
| query flag | `0x01` |
| report length | 32 bytes |

### Query flow

```text
enumerate VID/PID
      │
      ▼
prefer known col04 endpoint
      │
      ▼
send feature report 0x05
      │
      ▼
read feature report 0x05
      │
      ▼
validate battery / charging / full / online
```

PM1はComposite HIDとして複数endpointを公開するため、既知endpointがない場合は候補へqueryし、report contractを満たしたendpointだけを採用します。

### Response fields used by the implementation

`hid_protocol.parse_battery_report()` は少なくとも14 bytesのresponseを要求し、次を検証します。

- index 9: battery, `0..100`
- index 10: charging, `0/1`
- index 11: full, `0/1`
- index 12: online, `0/1`

範囲外値やboolean fieldの異常値は、もっともらしいbattery値へ丸めず `invalid_report` とします。

## Evidence policy

このrepositoryでは、次を区別します。

- **verified**: 実機receiverで取得を確認
- **compatible mapping**: protocol familyの既存mappingはあるが、このrepositoryでは未実機確認
- **unsupported**: 接続方式またはreport formatを確認していない

VID/PIDが同じだけではverified扱いにしません。firmware/revisionでpacket layoutが変わる可能性があるためです。
