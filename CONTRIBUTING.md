# Contributing

Issue / Pull Requestを歓迎します。特に新しいmouse modelを追加する場合は、**model名だけではなく実機evidence**を残してください。

## Development setup

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m pytest tests
```

## Before opening a PR

最低限、次を通してください。

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest tests
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

実機対応を変更した場合は:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe scripts\check_real_device.py
```

## Adding device support

PRには可能な範囲で次を含めてください。

- exact product/model name
- connection mode: 2.4 GHz / wired / Bluetooth
- VID/PID
- interface number / usage page
- sanitized raw HID report
- expected battery percentage at capture time
- parser unit test
- 実機で成功した `check_real_device.py` の結果

serial number、Windows user path、個人識別情報は貼らないでください。

## Design rule

device固有処理はprotocol adapterへ閉じ込め、`app.py` やtray UIへVID/PIDやraw packet layoutを持ち込まないでください。

新しいadapterは共通result shapeを返します。

```python
{
    "status": "connected",
    "device": "Model Name",
    "battery": 80,
    "charging": False,
    "full": False,
}
```

## Verification language

未実機確認のmodelを `verified` と表記しないでください。compatibleなVID/PIDやupstream mappingだけの場合は、その旨を明示してください。
