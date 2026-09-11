# Codex Desk Meter

책상 위에서 Codex 사용량과 리셋 상태를 확인하는 물리 장치 프로젝트입니다. 현재
기준 장치는 Waveshare ESP32-S3-LCD-3.16(Version 2)이며, Version 1
ESP32-S3 Super Mini 조립형 장치는 Version 2 검증 뒤 이식합니다.

## 현재 단계

현재는 benchmark 운영 도구 구현·검증 단계입니다. 합의한 agent/model 브랜치와
날짜 기반 run ID는 [브랜치·결과 관리 기준](docs/experiments/benchmark-management.md)을
따릅니다. schema v2와 실행기는 구현되었고, 도구별 모델·sandbox 검증 및 새 baseline
확정이 남아 있습니다. [실행 가이드](docs/experiments/agent-run-commands.md)의 gate를 통과한 뒤 pilot을 실행합니다.

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
.\scripts\check-experiment-preflight.ps1
```

이미 설치된 환경에서는 EIM 설치 단계를 건너뛰고 활성화부터 실행합니다. 보드가
없는 PC에서는 preflight가 이를 경고로만 표시합니다. 실제 COM3 검증은 다음처럼
명시적으로 요청합니다.

```powershell
.\scripts\check-experiment-preflight.ps1 -RequireHardware -Port COM3
```

## 문서 안내

- [프로젝트 목적](docs/PROJECT_PURPOSE.md)
- [Version 2 제품 계약과 합격 기준](docs/PRODUCT_CONTRACT.md)
- [Windows 개발 환경](docs/DEVELOPMENT_ENVIRONMENT.md)
- [Version 2 하드웨어 기능 카탈로그](docs/hardware/version-2-capabilities.md)
- [제조사 예제 및 bring-up 기록](docs/hardware/waveshare-manufacturer-example.md)
- [에이전트 실험 프로토콜](docs/experiments/agent-experiment-protocol.md)
- [브랜치·반복 실행·결과 게시 및 전환 항목](docs/experiments/benchmark-management.md)
- [에이전트 실행 명령 템플릿](docs/experiments/agent-run-commands.md)
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

실험을 시작하기 전에 기준 커밋을 태그하고, 각 실행마다 독립 worktree를 만듭니다.
공통 프롬프트의 `<run-id>`는 실행 manifest의 실제 ID로 치환합니다.

```text
experiments/fixtures/                 고정된 비공개 데이터 대체 입력
experiments/schema/                   manifest·결과 스키마
experiments/examples/                 validator용 예시
docs/agent-runs/<run-id>/             사람이 읽는 선택·검증 기록
results/<run-id>/                     구조화된 실행 결과
```

에이전트 비교에는 Codex CLI, Gemini CLI, Antigravity, OpenCode를 대상으로 하며
사용한 제품/CLI/IDE 표면까지 정확히 기록합니다. 일반 ChatGPT 웹 대화는 로컬
저장소·COM3·토큰 계측 조건이 달라 기본 비교군에 포함하지 않습니다.

고정된 예시 결과의 형식은 다음 명령으로 검사할 수 있습니다.

```powershell
python scripts\validate-experiment-result.py
```

확정된 실행 profile과 baseline을 준비한 뒤 다음 명령으로 pilot 디렉터리를 생성합니다.

```powershell
.\scripts\new-experiment-run.ps1 `
  -Baseline <baseline-tag> -Profile <profile.json> `
  -RunRoot C:\Espressif\benchmark-runs -Seed 20260911 -Phase pilot
```

이 명령은 새 독립 checkout과 운영 manifest를 생성합니다. 에이전트 실행은
별도 `benchmark.py run` 명령이며 도구별 sandbox 검증 receipt가 필요합니다.

## 데이터 출처 주의

`codex-reset.com`과 `codex-resets.com`은 서로 다른 독립 서비스입니다. 개인 계정
사용량은 공개 리셋 서비스가 제공하지 않으므로 실험에서는 fixture를 사용하고,
실제 계정 연동은 소유자가 별도로 통합 시험합니다. 리셋 예측은 일정 보장이 아닌
공개 신호·이력 기반 확률로 표시합니다.

## 라이선스와 비밀정보

Wi-Fi 자격증명, 계정 쿠키, API 키와 개인 사용량 원본은 커밋하지 않습니다. 제조사
예제와 출고 펌웨어 백업은 저장소 밖에 보관합니다. 공개 배포 전에 프로젝트
라이선스를 별도로 결정합니다.
