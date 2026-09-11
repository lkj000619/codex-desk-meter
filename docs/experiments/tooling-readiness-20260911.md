# 2026-09-11 운영 도구 구현 점검

제품 pilot 이전의 운영 도구 검증 기록이다. 에이전트 제품 구현 실행 결과가 아니다.

## 구현

- schema v2: 날짜 기반 ID, operator 실행 상태, nullable 미측정 값, 실제 JSON Schema 검증
- run 준비: 단일 root의 반복 번호 예약, 독립 Git snapshot, 원본/로컬 SHA, prompt 해시 분리
- 실행기: UTF-8 stdin, 외부 stdout/stderr, 단조 시간, 실패/중단/timeout 보존, 버전/profile/receipt gate
- Codex usage 정규화: input/output 합계, cache 중복 제외, 미제공 값 null
- 공통 평가: 제품 host 어댑터 계약, 고정 fixture와 시각, 오류/복구 검사 및 실물 채점표
- 로컬 보존: bundle, agent/model bare archive 브랜치, 이전 결과 누적과 새 구현 교체
- 결과 인덱스와 운영자 검토용 요약 생성

## 확인

ESP-IDF 환경 활성화 후 다음 명령으로 운영 도구 시험 20개와 schema v2 예제를 검증했다.

```powershell
. .\scripts\activate-idf.ps1
python -m unittest discover -s scripts/tests -v
python scripts/validate-experiment-result.py
```

통합 시험은 임시 저장소에서 r01/r02를 예약하고 각각 이력이 하나이며 remote가 없는지
확인한다. 두 실행을 같은 보관 브랜치에 저장한 뒤 이전 결과는 남고 이전 제품 소스는
남지 않는지 검사한다. synthetic subprocess로 UTF-8 입력·종료 코드·timeout을 검사한다.
이 시험은 모델을 호출하지 않으며 사용량 비교에 집계하지 않는다.

로컬 CLI: Codex 0.153.2, Gemini 0.35.0, OpenCode 1.18.30. agy 실행 파일과
print/stream-json/sandbox help도 확인했다. 정확한 agy 버전 확인은 남아 있다.
COM3는 초기 점검에서 없었지만 후속 점검에서 USB 직렬 장치로 감지되었다.
Docker CLI는 있지만 Docker Desktop Linux 엔진 연결은 실패했다. Docker가 유일한
허용 sandbox라는 뜻은 아니며, 실제 선택한 격리 환경의 증거가 필요하다.

## 남은 실행 gate

1. 도구별 정확한 모델 ID와 reasoning, 제공자 및 설정 profile 확정
2. 도구별 실제 sandbox 안의 최소 빌드, 권한·읽기 격리·네트워크 검증 및 receipt
3. Gemini/OpenCode/agy 입력 전달과 telemetry 형식 검증
4. 새 baseline 고정 후 도구별 pilot
5. 제품 구현과 실제 어댑터 연결 검토, COM3 실물 평가

현재 공통 평가 도구 자체 시험은 통과했으나 아직 제품 펌웨어를 평가한 것은 아니다.
본 실험은 pilot 합격 후 별도로 진행한다. 기존 baseline 태그는 보존한다.
