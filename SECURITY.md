# Security Policy

## Scope

Mouse Battery TrayはWindows user session内でUSB/HID deviceを読み取り、tray UIへ表示するlocal utilityです。通常のmonitoring pathはremote APIへdevice情報やbattery値を送信しません。

security issueとして特に重要なのは次です。

- arbitrary command execution
- unsafe startup registration
- writable path / DLL loading issue in packaged build
- malicious config handling
- unintended network transmission
- privilege escalation or UAC boundary issue

## Reporting

公開Issueへexploit detail、device serial、credential、個人情報を貼らないでください。

GitHubのSecurity Advisory / private vulnerability reportingが利用できる場合はそれを使用してください。利用できない場合はrepository ownerのGitHub profile経由で非公開の連絡手段を確認してください。

## Supported version

最新のdefault branchと最新Releaseを対象に修正します。過去buildへのbackportは原則として行いません。

## Private vulnerability reporting

Please report suspected vulnerabilities privately through GitHub's private vulnerability reporting form:
https://github.com/misaka310/mouse-battery-tray/security/advisories/new

Do not disclose exploit details, credentials, tokens, personal data, or other sensitive information in a public issue.
We aim to acknowledge a vulnerability report within 7 days, complete the initial assessment within 30 days, and coordinate disclosure after a fix is available, normally within 90 days. If remediation needs longer, we will communicate the revised disclosure timeline through the private report.
