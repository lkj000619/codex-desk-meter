# Codex Desk Meter

책상 위에서 Codex 사용량과 리셋 상태를 확인하는 물리 장치 프로젝트입니다. 현재
기준 장치는 Waveshare ESP32-S3-LCD-3.16(Version 2)이며, Version 1
ESP32-S3 Super Mini 조립형 장치는 Version 2 검증 뒤 이식합니다.

## 현재 단계

현재는 **에이전트 실험 실행 전 계획·readiness 문서 보완 단계**입니다. 아직 어떤
에이전트에게 공통 prompt를 전달하거나 COM3에 펌웨어를 올릴 단계가 아닙니다. 실행
가능 여부는 [실행 전 gate](docs/experiments/benchmark-readiness.md)의 R0~R10으로
판정하며, `AUTHORIZED`가 되기 전에는 `benchmark.py run`과 수동 prompt 입력을
실행하지 않습니다.

정식 기준은 `main`의 검토된 commit/tag입니다. 날짜 기반 run ID와
agent/model 브랜치 규칙은 [브랜치·결과 관리 기준](docs/experiments/benchmark-management.md)을
따릅니다. schema·runner의 일부 도구가 존재하더라도 그것은 제품 실험 승인을
의미하지 않으며, 기능별 결과·LCD GUI 기준과 PC integration 범위를 먼저 고정해야
합니다.

이 기준 브랜치는 제품 구현을 생성하기 위한 요구사항, 하드웨어 자료, 실험 기준과
재현 도구를 보관합니다. 에이전트가 작성한 펌웨어와 원본 실행 로그는 각 실험
브랜치에서 관리하고, 검증된 요약만 기준 브랜치에 반영합니다.

현재 저장소에는 아직 제품 펌웨어 프로젝트(`CMakeLists.txt`, `main/`)가 없습니다.
이는 Version 2 공통 프롬프트가 각 에이전트에게 동일한 기준에서 프로젝트를 만들고
검증하도록 하는 실험 조건입니다.

## 빠른 시작(Windows)

ESP-IDF 도구와 빌드 경로는 한글 경로 문제를 피하기 위해 ASCII 경로를 사용합니다.

```powershell
git clone https://github.com/lkj000619/codex-desk-meter.git C:\src\codex-desk-meter
Set-Location C:\src\codex-desk-meter

winget install --id Espressif.EIM-CLI --exact `
  --accept-package-agreements --accept-source-agreements
eim install -p C:\Espressif -i v5.3.2 -t esp32s3 -n true -a true `
  --idf-features pytests --do-not-track true

. .\scripts\activate-idf.ps1
idf.py --version
python -m pip install -r scripts/requirements-benchmark.txt
python -m unittest discover -s scripts/tests -p "test_*.py" -v
python scripts/validate-end-to-end-result.py
python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json
python scripts/validate-experiment-result.py
.\scripts\check-experiment-preflight.ps1
```

이미 설치된 환경에서는 EIM 설치 단계를 건너뛰고 활성화부터 실행합니다. 보드가
없는 PC에서는 preflight가 이를 경고로만 표시합니다. 실제 COM3 검증은 다음처럼
명시적으로 요청합니다.

```powershell
.\scripts\check-experiment-preflight.ps1 -RequireHardware -Port COM3
```

## 문서 안내

- [문서 역할·상태와 읽는 순서](docs/DOCUMENTATION_MAP.md)
- [문서 검토 결과](docs/DOCUMENTATION_REVIEW.md) · [진행·재개 체크리스트](docs/DOCUMENTATION_REVIEW_CHECKLIST.md)
- [프로젝트 목적](docs/PROJECT_PURPOSE.md)
- [Version 2 제품 계약과 합격 기준](docs/PRODUCT_CONTRACT.md)
- [Windows 개발 환경](docs/DEVELOPMENT_ENVIRONMENT.md)
- [Version 2 하드웨어 기능 카탈로그](docs/hardware/version-2-capabilities.md)
- [제조사 예제 및 bring-up 기록](docs/hardware/waveshare-manufacturer-example.md)
- [에이전트 실험 프로토콜](docs/experiments/agent-experiment-protocol.md)
- [실험 실행 전 readiness gate](docs/experiments/benchmark-readiness.md)
- [브랜치·반복 실행·결과 게시 및 전환 항목](docs/experiments/benchmark-management.md)
- [Version 2 기능·LCD GUI 비교 기준](docs/experiments/feature-comparison.md)
- [PC 수집기·ESP32 통합 계약 초안](docs/experiments/integration-contract.md)
- [에이전트 실행 명령 템플릿](docs/experiments/agent-run-commands.md)
- [에이전트 사용법·계측·권한 옵션](docs/experiments/agent-usage-and-permissions.md)
- [하드웨어 자율 기능 실험](docs/experiments/hardware-feature-discovery.md)
- [Version 2 공통 에이전트 프롬프트](experiments/prompts/version-2-agent-task.md)
- [실험 기준 설정](experiments/config/version-2-baseline.yaml)

## 제조사 예제 확인

공식 Demo ZIP은 저장소에 넣지 않고 `C:\Espressif\vendor` 아래에 보관합니다.

```powershell
. .\scripts\activate-idf.ps1
.\scripts\fetch-waveshare-demo.ps1
.\scripts\build-waveshare-example.ps1 -Example factory
```

이 명령은 빌드만 수행하며 보드에 플래시하지 않습니다. 플래시와 모니터는 실험
프로토콜과 백업 정책을 확인한 뒤에만 실행합니다.

## 에이전트 실험

아래 내용은 실행 절차의 개요일 뿐이며, [readiness gate](docs/experiments/benchmark-readiness.md)의
모든 조건과 사용자 승인이 있기 전에는 실행하지 않습니다. 공통 prompt는 사람이
복사해 CLI에 붙여넣지 않고, 검증된 runner가 실제 run manifest와 함께 정확히 한 번
전달합니다. 실행 중 maintainer/evaluator가 구현 방향을 알려주거나 코드를 고치면
해당 run은 정량 비교에서 제외합니다.

승인된 실험은 기준 커밋을 태그하고, 각 실행마다 독립 worktree를 만듭니다.
공통 프롬프트의 `<run-id>`는 실행 manifest의 실제 ID로 치환합니다.

```text
experiments/fixtures/                 고정된 비공개 데이터 대체 입력
experiments/schema/                   manifest·결과 스키마
experiments/examples/                 validator용 예시
docs/agent-runs/<run-id>/             사람이 읽는 선택·검증 기록
results/<run-id>/                     구조화된 실행 결과
```

현재 계획의 기본 비교 후보는 Codex CLI, Antigravity CLI, OpenCode CLI이며,
Gemini CLI는 Enterprise/API 키 조건의 별도 후보입니다. 최종 모델·설정은
[profile 검토 기록](docs/experiments/r4-profile-resolution.md)에 따라 확정합니다.
사용한 제품/CLI/IDE 표면까지 정확히 기록합니다. 일반 ChatGPT 웹 대화는 로컬
저장소·COM3·토큰 계측 조건이 달라 기본 비교군에 포함하지 않습니다.

고정된 예시 결과의 형식은 다음 명령으로 검사할 수 있습니다.

```powershell
python scripts\validate-experiment-result.py
```

확정된 실행 profile과 baseline을 준비한 뒤, 모든 readiness gate가 통과하고 사용자가
특정 pilot 실행을 승인한 경우에만 다음 명령으로 pilot 디렉터리를 생성합니다.

```powershell
.\scripts\new-experiment-run.ps1 `
  -Baseline <baseline-tag> -Profile <profile.json> `
  -RunRoot C:\Espressif\benchmark-runs -Seed 20260911 -Phase pilot
```

Non-executable profile templates and the read-only preflight input inventory are
kept in [`experiments/config/runner-profiles/`](experiments/config/runner-profiles/)
and [`experiments/config/preflight-inputs.example.json`](experiments/config/preflight-inputs.example.json).
They intentionally leave model, version, executable, and telemetry availability as
operator checks; they do not authorize a run.

기본 실행은 현재 main의 고정 문서·입력을 전용 branch/worktree에 제공하고,
프롬프트로 다른 branch·이전 결과 참조를 제한하며 명령·자료를 기록합니다.
Docker/VM은 선택 사항이며, 동일 조건과 충분한 증거를 갖춘 기본 모드 실행도
정량 비교에 사용할 수 있습니다. [실행 환경 정책](docs/experiments/isolation-policy.md)을 따릅니다.

이 명령은 새 독립 checkout과 운영 manifest를 생성합니다. 에이전트 실행은
별도 `benchmark.py run` 명령이며 선택한 접근 정책의 preflight receipt가 필요합니다. 이
README의 명령을 실행했다고 해서 제품 구현·하드웨어 검증이 완료되는 것은 아닙니다.

## 데이터 출처 주의

`codex-reset.com`과 `codex-resets.com`은 서로 다른 독립 서비스입니다. 개인 계정
사용량은 공개 리셋 서비스가 제공하지 않으므로 실험에서는 fixture를 사용하고,
실제 계정 연동은 소유자가 별도로 통합 시험합니다. 현재 검토 중인 E2E 계약은
`codex-resets.com`의 최근 리셋과 경과 시간을 표시합니다. `codex-reset.com`의
예측은 파서 호환용으로 보존하며 화면에는 표시하지 않습니다.

제품의 실제 데이터 경로는 `PC provider collectors → 정규화 snapshot → USB serial
(COM3) cdm/1 transport → ESP32 receiver/cache/stale → LCD GUI`입니다.
local Wi-Fi는 후속 별도 cohort입니다. USB·화면 계약의 선택값과 ADR 승인·baseline
동결 상태는 [문서 안내](docs/DOCUMENTATION_MAP.md)에서 구분합니다.
historical firmware-only 자료는 이 경로 중 fixture·firmware·GUI만 다룹니다.
정식 end-to-end benchmark는 PC collector와 transport/receiver까지 포함해야 하며,
이를 구현·검증하지 않은 상태에서 “실시간 계정 사용량 표시 완료”라고 주장하지
않습니다. 범위와 기능별 비교는
[기능·LCD GUI 비교 기준](docs/experiments/feature-comparison.md)을 따릅니다.

제품 이름은 현재 `Codex Meter`이지만 collector와 화면 모델은 Codex 전용으로
고정하지 않습니다. Codex CLI, Claude Code, Gemini CLI, Orca/IDE 등은 독립 provider
adapter로 연결하며, source가 실제로 제공하는 quota window·percent·token·credit만
표시합니다. 공개되지 않은 “남은 토큰량”을 임의로 추정하거나 서로 다른 metric을
합산하지 않습니다.

## 라이선스와 비밀정보

Wi-Fi 자격증명, 계정 쿠키, API 키와 개인 사용량 원본은 커밋하지 않습니다. 제조사
예제와 출고 펌웨어 백업은 저장소 밖에 보관합니다. 공개 배포 전에 프로젝트
라이선스를 별도로 결정합니다.
