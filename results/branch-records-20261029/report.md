# 2026-10-29 브랜치 기록의 main 반영

확인 범위는 원격 fetch 후 로컬 11개, 원격 25개 브랜치와 등록 worktree 8개다.
`origin/HEAD`는 브랜치 수에서 제외했다. 전체 SHA, 기존 main 대비 커밋 수,
동결 tag 20개와 worktree 상태는 [브랜치 목록](branch-inventory.json)에 보존한다.

## main 반영 범위

기존 main `681be53`에서 정식 비교 준비·실행 기록 42커밋과 Argon 기록 3커밋을 반영했다.
직접 후손인 `2847fea90a26604df947f5207fa724b2e0c870d3`까지 fast-forward하므로
원본 커밋과 evidence 바이트를 유지한다. 이번 정리 문서는 그 위에 별도 커밋으로 남긴다.

| 로컬 브랜치 | 확인한 끝 커밋 | 처리 |
|---|---|---|
| `main` | `681be53` | 정식 비교·Argon 45커밋과 이번 정리 기록 반영 |
| `prepare/formal-comparison-20261004` | `b933eac` | 정식 비교 기록을 main에 포함, 원본 브랜치 유지 |
| `lkj000619/test-gemini-4-argon-20261016` | `2847fea` | 시작·종료·실물·영상 평가를 main에 포함, 원본 브랜치 유지 |
| `lkj000619/experiment-orca-harness-20261008` | `470babd` | 결과를 아래에 기록하고 이력·소스·동결 tag를 bundle로 보관 |
| `docs/architecture-review-20261002` | `d6da44a` | 기존 main 이력에 포함됨 |
| `docs/verification-20260916` | `8a34fbc` | 기존 main 이력에 포함됨 |
| `main-2` | `c0ba9e2` | 기존 main 이력에 포함됨 |
| `experiment/20260911T030200Z-codex-pilot` | `abed99c` | 기존 main 이력에 포함됨, worktree의 미커밋 자료 유지 |
| `experiment/opencode/cli/muse-spark-1-3-contributor-free` | `c1be786` | 기존 main 이력에 포함됨 |
| `experiment/antigravity/cli/gemini-3-8-flash-high` | `499e39b` | 독립 실험 소스와 기존 원격 브랜치 유지 |
| `lkj000619/codex-reference-20260929` | `7923f96` | reference 구현과 기존 원격 브랜치 유지 |

원격 정식 실험 소스 17개는 [기존 게시 목록](../formal-comparison-20261004/branch-publication-20261008.md)을 따른다.
기존 reference와 pilot을 포함한 구현은 비교 원본으로 유지한다.
이번 반영은 이 소스들을 main의 제품 구현으로 채택하는 작업이 아니다.

## 확인한 결과와 남은 조건

| 기록 | 마지막 원본 관측과 판정 |
|---|---|
| [정식 비교](../formal-comparison-20261004/report.md) | 2026-10-08 첫 블록 5개 모델, 최초 5회와 후속 12회로 총 17회 종료. Series 5/15이며 전체 3블록 비교는 미완료다. 비용 coverage 16/17, 알려진 token 62,535,521, 전체 비용 합계는 미상이다. |
| [Gemini 4 Argon 평가](../gemini-4-argon-20261016/evaluation-20261016/report.md) | 2026-10-16 최초 실행과 실물·영상 평가 완료. Reference 미도달, `product_pass=false`. 입력 수락 뒤 stack overflow와 재부팅을 4회 확인했다. 영상에서 glyph 손상을 확인했고 RM1 pass, RM2 partial, RM3·RM4 fail, RM5 not_run이다. 후속은 0회 사용했으며 최대 3회·누적 7,200초가 남았다. |
| Orca 역할 협업 | 2026-10-10 17:12 KST 기준 Task 26개 구현·독립 검증 완료. PC 64/64와 당시 통합 27/27 통과, LCD 숫자 잘림·점멸 수정본을 업로드했다. 35.25초 영상과 직접 응답 범위에서 숫자·화면 순환·CRC VALID·반복 점멸 소멸을 확인했다. 지연·물리 오류복구·센서 검교정·24시간은 미측정으로 `product_pass=false`다. |

Argon과 Orca는 기존 정식 비교의 반복 수나 비용에 소급 합산하지 않는다.
실물 상태와 live 터미널은 위 날짜의 관측이다. 이번 작업은 모델 호출, 업로드, serial 열기와 계정 수집을 수행하지 않는다.

## Orca 원본 보관과 복원

Orca는 baseline `272875140d1998d458e26fdb2f6deab5e5d8f7b5`에서 분기한 독립 구현이다.
해당 브랜치의 정리는 main에 필요한 기존 문서·도구·결과를 삭제한다.
전체 병합 대신 [Git bundle](orca-harness.bundle)에 baseline 이후 이력 78커밋과
host·점멸·숫자 후보 및 snapshot tag 4개를 보관한다.

Bundle은 1,912,295 bytes이며 SHA-256은 다음과 같다.

```text
4d07b0efb7328443fb4332e63b2f2e5a5284563a98283e8d8f5f668fd3aa519e
```

이 bundle은 증분 형식이다. main에 남아 있는 위 baseline과 그 이력이 prerequisite다.
추적한 문서·source·시험·운영 근거는 복원할 수 있다.
Git에서 제외한 개인 runtime 자료와 다른 worktree의 미커밋 자료는 포함하지 않는다.

main 저장소에서 원본을 별도 브랜치로 복원하는 명령은 다음과 같다.

```powershell
git bundle verify results/branch-records-20261029/orca-harness.bundle
git fetch results/branch-records-20261029/orca-harness.bundle refs/heads/lkj000619/experiment-orca-harness-20261008:refs/heads/archive/orca-harness-20261008 'refs/tags/*:refs/tags/*'
git show archive/orca-harness-20261008:docs/experiments/orca-harness-results.md
```

복원한 브랜치의 문서 지도는 `docs/DOCUMENTATION_MAP.md`다.
결과는 `docs/experiments/orca-harness-results.md`, 재개 절차는
`docs/experiments/orca-harness-resume.md`, 원본 근거는 `experiments/orca-harness-20261008/`에 있다.
별도 bare 저장소에서 bundle을 가져와 끝 커밋 `470babd`와 결과 문서를 읽는 검증을 수행했다.
검증 저장소는 기존 baseline 객체를 공유했다. Bundle 단독으로 전체 저장소를 복원하는 검증은 아니다.

## 보존과 검증

다른 worktree의 변경·미추적 자료와 모든 기존 브랜치를 유지한다.
Argon worktree는 `core.longpaths=true`로 다시 조회하면 변경이 없다.
기본 Windows 경로 처리에서 보인 삭제는 이번 main 반영에 사용하지 않는다.

전체 도구 시험은 224개 중 221개 통과, 1개 건너뜀, 2개 오류다.
두 오류는 현재 HEAD를 archive로 추출할 때 생기는 Windows 긴 경로 문제다.
같은 두 시험의 오류가 [2026-10-16 원본](../gemini-4-argon-20261016/unittest-current-branch-path-errors.txt)에도 있다.
이번 실행의 [전체 로그](tool-tests.log)를 보존하며 도구 코드는 수정하지 않았다.

계약 검사와 main 반영 후 원본 비교 결과는 [검증 기록](verification.json)에 남긴다.
정식 비교·Argon 기록 3,590개는 Git 원본과 바이트 단위로 일치했다.
기존 tag 20개와 소스 브랜치를 보존했고 계약 예제·provider fixture 검사는 통과했다.
[작업 계획](../../docs/plans/2026-10-29-main-records-consolidation.md)의 완료 조건에 따라 확인한다.
