# 검증 결과 인덱스

현재 게시된 본 실험 결과는 없다. 실험 원본은 agent/model 보관 브랜치에서 관리한다.
main에는 운영자가 확인한 요약과 고정 commit 링크만 추가한다.

`python scripts/summarize-benchmark.py <manifest> ... --output <new-summary.md>`로
초안을 만든 뒤 C1~C8, 자율 기능 점수, 판정자, 평가 버전, 증거 링크, 토큰 정의와
측정 한계를 검토해서 추가한다. 이 명령은 자동 commit/push/merge하지 않는다.
완료 run의 중앙값·범위와 성공/전체 시도 수를 함께 집계하고 pilot은 제외한다.
