# Repository instructions

## 仕様の正本

- 仕様の正本: `README.md`
- 実装前に意図する仕様を正本へ反映し、仕様変更時は同じ変更で正本と検証を更新する。

## Repository boundaries

- このリポジトリの責務と既存の利用者向け挙動を維持する。
- README、CONTRIBUTING、docs、既存テストに矛盾がある場合は、実装だけを正として進めず差分を解消する。

## Absolute input-injection prohibition

- **ユーザーの実ホスト上で、マウスまたはキーボード入力を注入・擬似操作してはならない。例外なし。**
- 禁止対象には `pywinauto.click_input`, `send_keys`, `pyautogui`, `pynput`, Win32 `SendInput`, `mouse_event`, `keybd_event`、その他同等の入力注入APIを含む。
- GUI検証のためであっても、実ホスト上では上記APIを使用しない。
- GUIの実操作が必要な確認は、ユーザーの実セッションから隔離された専用VM/サンドボックスへ移す。VMが利用できない場合はその検証を実行せず、未検証として明示する。
- エージェントはVM内であっても入力注入を自動実行しない。必要なら人間による手動確認手順として文書化する。
- 実ホストで許可する自動検証は、unit test、process/state inspection、HID read、EXE smoke、UI objectの生成/破棄など、入力注入を伴わないものに限る。
- この禁止事項は速度、E2E達成、CI都合、過去実装との互換性より優先する。

## Verification

- リポジトリに記載されたtest、build、lint、typecheck、E2Eの入口を使用する。
- 仕様、実装、テスト、利用者向け文書が一致するまで完了扱いにしない。
- `tests/test_no_input_injection.py` を必ず維持し、禁止APIの再混入をCIで失敗させる。
