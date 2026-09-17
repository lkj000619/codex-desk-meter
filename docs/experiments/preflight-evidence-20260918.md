# Preflight 증거 기록 (2026-09-18, pilot 준비)

`check-experiment-preflight.ps1` 실행 + 읽기 전용 실측. 본 기록은 통과 선언이
아니다. R5는 검토된 policy-bound receipt가 있어야 닫히며, R10은 `not_authorized`
유지다.

## 실행 결과 요약

| 항목 | 결과 |
|---|---|
| 필수 파일 20종 존재 | 전부 OK |
| README UTF-16 검사 | OK |
| example manifest/result validator | OK (exit 0) |
| unittest 58개 | OK (exit 0, `PYTHONUTF8=1` 필요) |
| E2E validator + matrix validator | OK (exit 0) |
| COM3 | 포트 존재·상태 OK 탐지. 보드 모델·독점 점유는 pilot 직전 별도 확인 |
| 작업 트리 clean | **FAIL** — untracked 3건 (`.agents/`, `.claude/`, `skills-lock.json`) |
| ESP-IDF v5.3.2 활성화 | **FAIL** (아래) |

## FAIL 1: 작업 트리

baseline 태그 전에는 `git status --porcelain`이 비어야 한다. `.agents/`(archify
스킬 등), `.claude/`, `skills-lock.json`은 로컬 tooling 잔재로, `.gitignore`
추가 또는 정리 후 재확인한다.

## FAIL 2: ESP-IDF 활성화 → 수리 완료 (2026-09-18)

- 원인: EIM 프로필 파싱 오류 + Rust xtensa wrapper의 한글 경로 패닉 +
  `xtensa-esp-elf-gdb` 등 일부 도구 미설치.
- 수리: `idf_tools.py install`·`install-python-env`로 사용자 `.espressif` 보완,
  ASCII junction `C:\Espressif\user-tools` 생성, 수동 환경 구성
  (`DEVELOPMENT_ENVIRONMENT.md` ASCII junction 절 참조).
- 검증: `idf.py --version` → `ESP-IDF v5.3.2`,
  `hello-world` esp32s3 전체 빌드 성공 (`hello_world.bin`,
  `bootloader.bin`). 플래시 쓰기는 수행하지 않았다.
- 남은 과제: `activate-idf.ps1`가 여전히 깨진 EIM 프로필에 의존하므로,
  스크립트 수준의 수리(수동 환경 구성 반영)는 별도 작업으로 남는다.

## 입력 bundle SHA-256 (R1 보조, 동결 아님)

```
7E6354AEC3AD...  experiments/prompts/version-2-agent-task.md
3635BDCBA87B...  experiments/config/version-2-baseline.yaml
152D8C0C2F4F...  experiments/fixtures/provider-fixture-matrix.json
2A3CD59029B7...  experiments/schema/end-to-end-result.schema.json
```

전체 bundle 목록은 `check-experiment-preflight.ps1`의 requiredFiles와 동일하다.
동결은 별도 baseline 태그 시점에 전체 SHA로 기록한다.

## R10 조건부 승인 기록 (2026-09-18 사용자 승인)

사용자가 환경 수리(A안)와 pilot 실행을 승인했다. 단, 본 승인은 아래 전제조건이
모두 충족될 때 발효되는 조건부 승인이다. 미충족 상태에서 runner를 실행하지 않는다.

- 환경 수리 완료 (본 기록으로 확인. 단, `activate-idf.ps1`의 스크립트 수준 반영은
  잔여 작업으로 남는다. toolchain 동작 확인済み이나 스크립트 미수리 상태다.)
- 표면별 model 확정 (codex sol/luna, muse-spark 재확인, antigravity 3종)
- `benchmark.py prepare` 통과 + 새 baseline 태그·bundle hash 동결
- COM3 단독 점유 확인 (pilot 직전)

발효 시 pilot 범위: 위 모델 엔트리별 1회 (codex×2 + opencode×1 + antigravity×3).
발효 전까지 R10은 `not_authorized`를 유지한다.

## Settings inventory (읽기 전용 확인)

- codex 0.153.2 / opencode 1.18.31 / agy 1.2.4 실행 파일 경로 확인済み.
- gemini-cli 설치 파손 (비교군 제외, `r4-profile-resolution.md` 참조).
- skills/MCP/memory 등 표면별 설정 실측은 모델 확정 후 profile에 기록한다.
