# Preflight 증거 기록 (2026-09-18, pilot 준비)

`check-experiment-preflight.ps1` 실행 + 읽기 전용 실측. 본 기록은 통과 선언이
아니다. R5는 검토된 policy-bound receipt가 있어야 닫히며, R10은 `not_authorized`
유지다.

## 실행 결과 요약

| 항목 | 결과 |
|---|---|
| 필수 파일 21종 존재 | 전부 OK |
| README UTF-16 검사 | OK |
| example manifest/result validator | OK (exit 0) |
| unittest 58개 | OK (exit 0, `PYTHONUTF8=1` 필요) |
| E2E validator + matrix validator | OK (exit 0) |
| COM3 | 존재, 상태 OK (보드 연결됨) |
| 작업 트리 clean | **FAIL** — untracked 3건 (`.agents/`, `.claude/`, `skills-lock.json`) |
| ESP-IDF v5.3.2 활성화 | **FAIL** (아래) |

## FAIL 1: 작업 트리

baseline 태그 전에는 `git status --porcelain`이 비어야 한다. `.agents/`(archify
스킬 등), `.claude/`, `skills-lock.json`은 로컬 tooling 잔재로, `.gitignore`
추가 또는 정리 후 재확인한다.

## FAIL 2: ESP-IDF 활성화

- `activate-idf.ps1` → EIM 프로필
  `C:\Espressif\tools\Microsoft.v5.3.2.PowerShell_profile.ps1:87`에서 파싱 오류.
  WinGet 설치 경로 문자열이 깨져 있으며 `chcp 65001`로도 해소되지 않는다.
- 대체 경로 `esp-idf\export.ps1`은 `xtensa-esp-elf-gdb` 미설치로 중단된다.
- 수리 없이 `idf.py` 빌드 게이트를 통과할 수 없다. 후보 조치:
  1. EIM CLI 재설치로 프로필 재생성, 또는
  2. `idf_tools.py install`로 gdb 포함 전체 도구 설치 후 export 경로 사용.
- 환경 변경이므로 사용자 승인 후 수행한다. 본 기록 시점에는 미수리.

## 입력 bundle SHA-256 (R1 보조, 동결 아님)

```
7E6354AEC3AD...  experiments/prompts/version-2-agent-task.md
3635BDCBA87B...  experiments/config/version-2-baseline.yaml
152D8C0C2F4F...  experiments/fixtures/provider-fixture-matrix.json
2A3CD59029B7...  experiments/schema/end-to-end-result.schema.json
```

전체 bundle 목록은 `check-experiment-preflight.ps1`의 requiredFiles와 동일하다.
동결은 별도 baseline 태그 시점에 전체 SHA로 기록한다.

## Settings inventory (읽기 전용 확인)

- codex 0.153.2 / opencode 1.18.31 / agy 1.2.4 실행 파일 경로 확인済み.
- gemini-cli 설치 파손 (비교군 제외, `r4-profile-resolution.md` 참조).
- skills/MCP/memory 등 표면별 설정 실측은 모델 확정 후 profile에 기록한다.
