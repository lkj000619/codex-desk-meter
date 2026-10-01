# 실험 전 설계 검토 후속 조치 — 2026-09-18

## 판단과 범위

프로젝트 목적→계약→입력→평가의 불일치를 보완했다. 아래 완료는 maintainer의
문서·host 도구·개발 환경 검증이며, candidate 구현·실물 제품 합격·pilot 실행을
뜻하지 않는다. 사용자 요청은 권장 순서대로 진행하는 것이며 추가 실행 승인을
반복 요청할 필요는 없다. 다만 미확정 모델/설정을 임의로 승인 완료로 기록하지 않는다.

## 검토 항목과 변경

| 항목 | 변경 | 확인 방법 | 상태 |
|---|---|---|---|
| I2/I3 wire 불일치 | usage 배열, GlobalResetSnapshot 논리↔wire 매핑 명시, 충돌 별칭 거부 | 매핑 round-trip 및 기존 frame golden test | 완료 |
| I3/I4 재시작 복구 | 장치별 송신 순번 영속화, 실패 시 번호 소비, 유실 시 전송 차단, 재열거 정책 | 같은 reference receiver에서 7→1 거부→8 수용 | 계약·host 규칙 완료; 영속 collector 및 실물 시험은 candidate/operator 수행 |
| F1 fixture 누락 | Antigravity unsupported 합성 입력, matrix 및 기본 registry 반영 | matrix validator, registry identity 확인 | 완료 |
| C8 수동 갱신 | BOOT 화면 전환과 PC 즉시 재수집을 분리, 시간 기준 명시 | 제품·prompt·평가 계약 대조 | 계약 완료; 실물 시험 대기 |
| G1~G6 관찰 편차 | 50cm·고정 조명/촬영·동일 과제, 식별 시간·blind run ID 기준 | rubric·기록 규칙 대조 | 계약 완료; 채점 대기 |
| R4 profile/runner | 실제 버전 문자열, Antigravity text stdin·120m timeout, unresolved 설정 거부 | profile 검증 회귀 시험 | 도구 수정 완료; 최종 설정 대기 |
| R5 환경 재현 | ASCII 설치를 통한 IDF 활성화, UTF-8 preflight, 고정 benchmark 패키지 설치 | 새 셸 활성화, 새 hello-world 빌드, 통합 preflight | host 환경 검증 완료 |

## 실행한 검증

- 공통 ESP-IDF Python 환경에서 전체 **63개 unittest 통과**.
- 기존 manifest/result validator, E2E result 및 provider matrix validator 통과.
- ESP-IDF v5.3.2 / xtensa GCC 13.2.0 / Ninja 1.12.1 확인.
- `C:/Espressif/smoke-tests/hello-world-v5.3.2/build-readiness-20260918`에서
  새 ESP32-S3 hello-world 빌드 성공(exit 0). COM3 전송·flash 없음.
- hello_world.bin SHA-256:
  `8C39CAD94991911E25A36C848DCE00DEA6D0D343E72B6F0390AA3B6D0D25B6D4`
- bootloader.bin SHA-256:
  `EB072C9954605174E3844B3CAD377553D31CEE9101DAC09059A43DFE6A087856`
- 빌드 raw log는 위 build 경로의 `log/idf_py_stdout_output_9520`,
  `log/idf_py_stderr_output_9520` 및 `*_11992`에 남는다.
- 통합 preflight의 수정 후 결과: 기능·환경 검사 통과, COM3 존재 확인.
  커밋 전에는 작업 트리 변경만 1개 gate 실패로 남았다. 포트 조회는 독점 점유
  또는 보드 모델 검증을 대신하지 않는다.

초기 제한 환경에서는 PowerShell/임시 Git 시험 접근이 막혔고, 정상 환경에서
재실행했다. 이어 IDF Python에 jsonschema가 없어 `scripts/requirements-benchmark.txt`
고정 버전을 설치한 뒤 동일 환경에서 전 검사를 통과했다. 이를 제품 실패로 집계하지 않는다.

## baseline과 pilot에 남은 조건

1. 정확한 모델·reasoning 확정. 기록된 Codex `sol/luna`, OpenCode
   `opencode/muse-spark-1.3-contributor-free` 외 Antigravity effort 변형 선택이 남았다.
   현재 후보: `gemini-3.8-flash-high/medium/low`, `gemini-3.1-pro-high/low`,
   `claude-opus-4-6-thinking`. 기본값을 명시적인 high/low 선택으로 오인하지 않는다.
2. 각 surface의 builtin-only-v1 실제 적용 증거: `--pure`나 정책 문구만으로
   skills/MCP/memory/hooks 전체가 비활성화되었다고 주장하지 않는다. 로컬 목록
   조회에서는 Antigravity MCP 및 imported plugins 없음이 출력되었으나 시작 로그에
   named hook 1개가 관측되었다. 이것만으로 R4/R5를 pass 처리하지 않는다.
3. 확정 profile과 baseline 해시에 묶인 preflight receipt, prompt 1회 전달과
   activity logging 검증, 동결 입력으로 prepare 완료.
4. pilot 직전 COM3 단독 점유·산출물 동일성 및 하드웨어 평가 준비 확인.

따라서 현재 변경을 보존하되 정식 baseline tag와 R10 발효를 선언하지 않는다.
기존 2026-09-18 조건부 pilot 승인 및 이번 진행 요청은 유지된다.

## 다음 담당 작업

maintainer는 모델 선택이 확정되면 surface별 격리 설정을 검증하고 실행 profile,
receipt와 baseline을 동결한다. runner는 모델 엔트리당 pilot 1회를 수행한다.
operator는 동결된 candidate 산출물에 대해 C/I/G 실물 평가를 수행한다.
각 단계의 기한은 다음 단계 시작 전이며 미충족 조건을 pass로 대체하지 않는다.
