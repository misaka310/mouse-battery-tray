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

X1側はbattery queryを送る方式ではなく、receiver endpointから届くbattery heartbeatを短時間待ちます。

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

## Archived device support

SPRIME PM1 support was retired from the active runtime on 2026-09-19. The last PM1-capable source, protocol notes, and tests are preserved on the `archive/sprime-pm1-final` branch for reference and possible future restoration.

