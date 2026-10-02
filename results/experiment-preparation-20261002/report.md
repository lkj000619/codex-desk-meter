# 본 실험 실행 준비 검증

확인일: 2026-10-02 KST. 상태: **실행 준비 완료·본 실험 시작 전 정지**.
사용자 요청에 따라 실행 설정을 준비했으며 제품 실험은 시작하지 않았다.
제품 공통 시작 commit은 `85ba1089226a2e3198983a42eea375a3fd7e6ed0`이다.
이후 준비 문서 커밋이 추가돼도 이 제품 입력 baseline은 바뀌지 않는다.

## 확인한 실행 표면

| 대상 | CLI 버전 | 고정 모델·effort | 실제 준비 검증 |
|---|---|---|---|
| Codex Sol | 0.159.2 | `gpt-5.6-sol`, medium | 읽기·쓰기·목록·host build/test·IDF build·제조사 source·settings·telemetry |
| Codex Luna | 0.159.2 | `gpt-5.6-luna`, max | 동일 9개 capability |
| OpenCode Muse | 1.18.34 | `opencode/muse-spark-1.3-contributor-free` | 동일 9개 capability |
| AGY Flash | 1.2.14 | `gemini-3.8-flash-medium` | 동일 9개 capability |
| AGY Pro | 1.2.14 | `gemini-3.1-pro-high` | 동일 9개 capability |
| AGY Opus | 1.2.14 | `claude-opus-4-6-thinking` | 동일 9개 capability |

검증 대상은 별도 ASCII 경로의 **빈 앱·산술 시험 fixture**다. 제품 source·이전 후보
구현은 제공하지 않았다. 각 CLI의 실제 도구 호출, CTest 통과, IDF build 완료와 생성 파일
hash를 [capability 목록](capability-summary.json)에 기록했다. process exit 0만으로
빌드 통과를 판정하지 않았다. 제품 BSP·LCD 기능 합격은 이 검증 범위에 포함되지 않는다.

[프로필](../../experiments/config/verified-profiles-20261002/)은 실제 설치 version/help와
모델 목록을 확인해 작성했다. AGY는 준비 도중 version guard에서 1.2.11→1.2.14 변경이
관측돼 1.2.14 실행본을 별도 경로에 고정하고 재검증했다. 변경 원인은 확정하지 않았다.
이전 선언으로 만든 AGY 예약 3개는 실행하지 않고 중지·대체 기록으로 보존했다.

## 설정과 권한

조건은 `builtin-only-v1`, 접근 정책은 `prompt-and-log`, `read_isolation: not_enforced`다.
설정 선언과 실제 inventory를 [원본 설정 근거](receipts/evidence/common/settings-inventory.json)로
연결했다. 외부 읽기가 OS 수준에서 완전히 차단된다고 주장하지 않는다.

- Codex: native `skills/list`로 사용자 스킬 9개 비활성·system 스킬 5개 활성 확인.
  `skip_host_skill_discovery`만으로 부족해 각 사용자 경로를 명시했다. workspace-write 범위의
  Windows elevated sandbox를 사용한다. unelevated의 Python pipe 거부는 실패 근거로 남겼다.
- OpenCode: 실행용 config root와 명시한 환경 8개를 고정했다. native inventory에서
  `customize-opencode` 내장 스킬만 확인했으며 plugin/MCP/외부 instructions는 비어 있었다.
  일반 인증 경로는 유지했고 credential 내용은 복사하지 않았다.
- AGY: 기존 scoped wrapper와 고정 permission policy를 사용했다. 준비 session마다 원래
  전역 설정·instructions·hooks를 복원했다. native MCP·imported plugin은 비어 있었으며
  추가 전역 AGENTS/rules/skills/agents 경로도 존재하지 않았다. private backup은 게시하지 않는다.
  이후 실행도 **benchmark 바깥을 이 wrapper로 감싸야** 한다. 프로필만으로 scope가 생기지 않는다.

## 공통 입력·예약·관측

[동결 목록](freeze.json)에 baseline, profile·receipt hash, prepared 디렉터리와 ledger,
실행 순서와 예산을 기록했다. 6개 후보의 공통 파일 57개는 bytes/hash가 같고 필수 MD는
3개다. 모델별 profile과 식별자가 달라 전체 input bundle hash는 서로 다르다.

순서는 baseline의 무작위 순서 조건에 따라 Python `random.Random(1).shuffle`로 고정했다:
Muse → Flash → Opus → Sol → Pro → Luna. 이는 첫 6개 후보 블록의 준비 목록이다.
3회 독립 반복의 완료나 최종 순위를 뜻하지 않는다. AGY run ID의 `r02`는 version 변경으로
예약을 대체한 식별자이며 실행된 두 번째 반복으로 세지 않는다.

최초 7,200초, 후속 최대 3회·후속 누적 7,200초의 기존 운영 조건을 ledger로 연결했다.
모든 후보는 `prepared`, `started_at: null`, 예약 소비 시간 0초이며 제품 실행은 0회다.
COM3는 USB VID_303A/PID_1001 연결을 열거해 확인했다. 준비 중 포트를 열거나 flash/erase/
제품 frame 전송을 수행하지 않았다. 단일 보드의 serial·광학 관측은 이후 후보 실행과
생성 artifact가 있을 때 공통 관측 절차로 수행한다.

## 검증 결과와 보존

깨끗한 별도 operator checkout에서 하드웨어 연결 확인을 포함한 전체 preflight를 실행했다:
**176개 시험 중 175개 통과·기존 Windows symlink 시험 1개 skip, 실패 0·경고 0**.
[원본 로그](receipts/evidence/common/clean-baseline-preflight.txt)는 원래 UTF-16LE bytes를 보존한다.
6개 receipt는 baseline/profile/input/reference hash와 capability evidence 연결을 validator로 확인했다.

[준비 package](preparation-package.zip)는 baseline의 operator source, 6개 candidate 파일 snapshot과 원래 Git commit bytes,
원래 manifest/profile/prompt/ledger/reference, receipt와 원본 준비 로그를 포함한다.
CLI 실행 파일·SDK 설치본·인증·private backup·사용자 설정 원본은 포함하지 않는다.
[package hash](package-metadata.json)를 확인한 뒤 [복원 검증기](audit_preparation.py)로 새 경로에
복원할 수 있다. 복원 검증은 provider나 보드를 실행하지 않는다.

```powershell
python -X utf8 results/experiment-preparation-20261002/audit_preparation.py `
  results/experiment-preparation-20261002/preparation-package.zip C:/meter-preparation-audit-new
```

독립 복원 결과는 [기계 검증 기록](restore-audit.json)에 보존한다. operator source 186개,
package 파일 325개와 6개 후보의 원래 commit/tree·receipt·fixture artifact hash를 확인했다.
package는 약 9.9 MiB다. [최종 별도 검토](final-review.md)는 Critical/Important/Minor 발견 사항 없이
준비 완료 판정을 지지했다. [최신 실행본·제조사 hash 확인](runtime-verification.json)도 통과했다.
게시 직전 원본/profile/receipt/package 파일 242개의 Git blob bytes도 일치했다.
선별한 빈 앱 artifact는 ignore 예외로 등록하며 hash에 묶인 JSON과 원본 로그는 줄바꿈 변환을 막았다.
원래 candidate commit/tree를 재구성하며 과거 parent 이력은 shallow 경계로 명시해 제외한다.
checkout 변환을 거치지 않고 원래 working bytes를 복원한다. 공통 입력의 LF와 생성 metadata의
CRLF를 각각 보존하고, 원래 Windows Git index 정규화로 commit/tree hash를 확인한다.
이 package는 준비 bytes의 복원을 검증하며, 아직 없는 제품 실행 artifact를 포함하는 terminal
evidence package를 대신하지 않는다. 후자는 실제 후보 종료 후 기존 도구로 만든다.

## 실패·미해결 위험

[전체 준비 시도](preparation-attempts.json)에 26개 CLI 준비 시도와 약 3,011.759초의
process 시간 합을 별도로 보존했다. 병렬 호출이 있어 이 합은 운영자 경과 시간과 다르다.
권한 거부·잘못된 준비 argv/vendor 경로·사용량 한도·컴파일러 오류를 성공 기록에서 지우지
않았다. 제품 최초/후속 예산에는 준비 비용을 넣지 않는다. terminal usage가 없으면 null이다.

Flash 준비에서 ESP-IDF SDK의 `rgb_panel_draw_bitmap` 컴파일 중 Xtensa GCC 내부 오류가
2회 관측됐다. 새 고정 실행본의 최종 probe는 첫 빌드에서 성공했지만 **컴파일러 결함을
수정했다는 뜻은 아니다**. 같은 source/flags를 사용한 직접 재현은 통과했고 실제 session의
TEMP/TMP도 ASCII 경로였다. 병렬 실행·한글 임시 경로를 원인으로 확정하지 않는다.
유사한 Windows LCD 소스 내부 오류와 재빌드 통과가 [ESP-IDF 공식 이슈](https://github.com/espressif/esp-idf/issues/16078)에
보고돼 있으나 현재 환경의 원인을 입증하지는 않는다. SDK/컴파일 flags/권한은 바꾸지 않았다.
실제 제품 실행에서 실패나 자체 재시험이 발생하면 원본 로그와 실제 예산에 보존하고
첫 결과를 새 실행으로 덮어쓰지 않는다.

Codex 준비 2개는 provider usage limit으로 실패했다. 안내된 reset 시각 뒤 새 session은
성공했다. 120분 연속 사용 가능한 quota를 예약하거나 보장한 것은 아니다.
새 Codex native `reasoning_output_tokens`는 원본과 capability의 `native_terminal_usage`에
보존했다. 고정 baseline의 정규화기는 이 새 필드를 매핑하지 않으므로 normalized reasoning
null을 provider 미계측이나 0으로 해석하지 않는다. provider별 total 정의도 섞지 않는다.

## 이후 시작할 때의 조건

사용자의 별도 본 실험 실행 지시 전에는 `benchmark.py run`을 호출하지 않는다.
현재 예약 ID는 **2026-10-02 KST에만 유효**하다. 다른 날에는 깨끗한 동일 baseline에서
새 날짜의 ID·ledger를 준비하고 input/comparison에 receipt를 다시 묶어 검증한다.
과거 예약이나 receipt를 날짜만 고쳐 재사용하지 않는다.

실행 직전 CLI version/executable hash, native 설정 inventory와 config root, 새로 설치된
사용자 스킬·MCP·plugin·AGY 추가 rules, SDK/vendor hash, ASCII TEMP, COM3 연결과 단일 보드
일정을 다시 확인한다. 설정이 달라지면 현재 receipt를 쓰지 않고 해당 조건을 재검증한다.
실제 사용자 인증은 해당 CLI의 정상 경로에서 사용하며 package로 이전하지 않는다.
공통 준비 때와 같은 활성화 shell에서 `scripts/activate-idf.ps1`을 적용하고
`IDF_TARGET=esp32s3`을 프로세스 환경에 설정한다. TEMP/TMP는 `C:/Espressif/tmp`,
IDF는 5.3.2·`C:/Espressif/user-tools`, ccache는 비활성인 조건을 유지한다.
