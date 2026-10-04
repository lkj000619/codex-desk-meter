# 2026-10-04 독립 최종 검토와 보완

검토 범위: E1~E5 통합 변경, native 권한, 후속 과제 전달, 적격성·비용 집계, package 독립 복원.
별도 검토 에이전트는 읽기 전용으로 재현했으며 모델 호출·전역 설정 변경·저장소 수정은 수행하지 않았다.

| 발견 | 영향 | 보완·검증 |
|---|---|---|
| P1: followup clone의 autocrlf 변환 | 최초 후속 호출 전 immutable hash 불일치로 차단 | 직전 고정 입력을 검증하고 원본 bytes를 복사. 강제 autocrlf 회귀의 수정 전 실패·수정 후 통과 확인 |
| P2: AGY wrapper 옵션 순서 | 문서의 run/restore 예제가 required backup-dir 오류 | 옵션을 positional action 앞에 배치하고 실제 help/parser와 대조 |
| P2: py_compile 탭 구분 | OpenCode 선언 map이 외부 경로를 허용 | 탭 포함 명령 거부. 수정 전 실패·수정 후 통과, 최종 설정으로 실제 OpenCode 빈 앱 검증 재실행 |

이 외 policy binding·과거 호환·package 보존·RM prefix 비용 집계에서는 중요한 추가 결함을 찾지 못했다.
검토가 에이전트의 모든 미래 행동을 보장하지 않는다. 접근 조건은 prompt-and-log이며 OS 격리 미적용이다.
최종 전체 회귀: 220개 중 219개 통과, Windows symlink 권한 제한 1개 skip, 실패 0개.
원본은 [tests-final.txt](tests-final.txt), 실행 상태는 [tests-final-status.json](tests-final-status.json)이다.
동결·당일 receipt·준비 package 복원은 별도 실제 실행 기록으로 확인한다.
