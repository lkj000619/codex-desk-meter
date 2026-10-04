# Codex Desk Meter

Waveshare ESP32-S3-LCD-3.16의 가로 LCD에 PC에서 전달한 사용량·글로벌 리셋·상태를
표시하는 ESP-IDF v5.3.2 제품과, 이를 구현하는 AI 에이전트의 첫 결과·후속 수정 비용을 비교한다.
main에는 요구사항·공통 입력·운영 도구를 보관한다. 후보 펌웨어와 실행 원본은 독립 run에서 관리한다.

## 후보가 받는 입력

필수 MD는 아래 **3개**다. runner는
[명시적 파일 목록](experiments/config/agent-inputs.json)만 candidate checkout에 복사한다.
운영·평가 문서, 과거 결과·증거, main의 Git 이력은 후보에게 복사하지 않는다.

| 문서 | 소유하는 내용 |
|---|---|
| [실행 과제](experiments/prompts/version-2-agent-task.md) | 목표·접근 범위·실행 방법·제출물 |
| [제품 계약](docs/PRODUCT_CONTRACT.md) | C/I/F 동작·데이터·전송·화면·검증 조건 |
| [보드 자료](docs/hardware/version-2-capabilities.md) | 핀·극성·설정 사실·제조사 source 범위 |

schema·fixture·예제와 필요한 host 시험 도구도 고정 목록으로 제공한다.
세 MD부터 읽고 구현하는 계층에 필요한 기계 입력만 참조한다.
기준 commit·목록·파일 hash는 운영자가 보존하며 실행 전/후 입력 변경을 검사한다.
이 제공 범위 제한은 외부 폴더 접근을 막는 OS sandbox를 뜻하지 않는다.

## 운영자가 확인할 상태

[다음 비교 준비 상태](docs/experiments/next-comparison-readiness.md) →
[운영 계약](docs/experiments/comparison-operating-contract.md) →
[수정 계획](docs/plans/2026-10-02-experiment-contract-remediation.md) 순서로 확인한다.
Codex에서 확인된 기능 도달과 전체 제품 합격은 별도로 판정한다.
최초 최대 120분, 후속 최대 3회·누적 120분이며 BSP 구현도 후보 작업에 포함한다.

후보 입력 제한, 기준 stimulus 복구, 후속 예산·reference 판정, 실패 비용 집계와
관측·복원 도구를 구현했다. [도구 안내](docs/experiments/comparison-tooling.md)에 명령과 증거 형식을 정리했다.
10월 4일에는 Claude를 제외한 활성 5개 모델의 실제 capability, 실행 경계 보완, 새 baseline 동결,
당일 ID·개별 ledger·receipt 연결과 독립 복원을 완료했다. Codex는 `gpt-6-sol` medium /
`gpt-6-luna` max다. [새 프로필](experiments/config/next-profiles-20261003/README.md)과
`comparison-baseline-20261004`를 사용한다. 10월 4일 COM3 연결을 확인한 뒤 22:47:50 KST에 첫 정식 실험 OpenCode Muse를 시작했다.
현재 실행·종료·평가 상태는 [정식 실행 기록](results/formal-comparison-20261004/report.md)을 따른다.
최신 상태와 보완 도구의 적용 범위는
[다음 비교 준비 상태](docs/experiments/next-comparison-readiness.md)가 관리한다.
후보 생산 코드 연결·실물 측정은 후보 실행 이후 수행한다.
기존 단회 pilot의 gate·원본 판정은 당시 기록이며 새 운영 계약을 대신하지 않는다.
실제 후보 실행·보드 업로드·계정 통합은 운영자가 별도로 관리한다.

전체 문서의 역할과 과거 기록은 [문서 지도](docs/DOCUMENTATION_MAP.md)를 따른다.
main에는 아직 제품 펌웨어 프로젝트가 없다. 후보는 동일한 시작 입력에서 직접 작성한다.

## Windows 준비·오프라인 검사

[개발 환경 안내](docs/DEVELOPMENT_ENVIRONMENT.md)대로 ASCII 경로에 SDK·toolchain을 준비한다.
아래 명령은 도구 회귀·예제 계약 검사이며 후보 실행이나 보드 flash를 시작하지 않는다.

```powershell
. .\scripts\activate-idf.ps1
python -m pip install -r scripts/requirements-benchmark.txt
python -m unittest discover -s scripts/tests -v
python scripts/validate-end-to-end-result.py
python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json
```

실제 계정 사용량은 이번 fixture 비교에 포함하지 않는다. API key·cookie·Wi-Fi credential·
개인 원본은 커밋하지 않는다. 제조사 source와 출고 backup은 저장소 밖에서 관리한다.
