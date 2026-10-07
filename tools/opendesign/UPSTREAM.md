# 고정 OpenDesign 원본

- source: https://github.com/manalkaff/opendesign
- commit: `cecd9bb6b59408cb96a3974449b8e6ef9f5b17bb`
- license: MIT, 원본 [LICENSE](LICENSE) 보존
- copied: `skills/` 원본 Markdown 10개와 `skills/opendesign/viewer.html`

전체 앱·global plugin·Node 의존성은 설치하지 않았다. 기존 원본 skill은 수정하지 않는다.
이번 실험의 적용 조건은 [협업 설계](../../docs/design/2026-10-08-orca-harness.md)와 각 Task가 소유한다.
추가 질문의 알려진 답변은 소유자의 820×320 LCD, 신규 구현, fixture/live 값의 의미 보존,
각 모델 후보 3개, 별도 브랜드 없이 다양한 탐색, 실제 하드웨어 구현 가능성과 가독성 우선이다.

embedded 시안은 HTML/CSS/소량의 native JavaScript로 충분하므로 React/Babel·CDN·웹폰트
설치를 하지 않는다. 화면 안의 색·타입·좌표·전환을 실제 LCD renderer로 옮길 수 있어야 한다.
원본의 setup/preview/verifier 역할은 실제 Orca Task로 조율하며, 단일 공유 manifest는
coordinator/지정된 viewer 담당자가 갱신한다. 디자이너끼리 동시에 덮어쓰지 않는다.
