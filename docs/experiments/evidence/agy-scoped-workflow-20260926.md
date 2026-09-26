# 제한 명령군·checkout 쓰기 정책 검증 — 2026-09-26

사용자가 요청한 "필요 명령 제한 유지: 조회·파일 생성·빌드·시험 명령군을 더
정리하고 별도 사전 검증"을 적용했다. 무제한 명령 허용이나 permission bypass는 사용하지 않는다.

## 실행 범위

- 읽기: 상대 경로 조회, 내용 확인, Test-Path/Get-Item/Resolve-Path/Get-FileHash.
- 생성: 상대 경로의 New-Item(File/Directory), mkdir. 내용 편집은 native 파일 도구.
- 빌드·시험: IDF 고정 동작과 -B, 제한된 CMake/CTest, unittest/py_compile/로컬 tests 파일,
  build-host 시험 실행 파일. shell 결합, 임의 Python, 설치/flash/history 조회는 포함하지 않는다.
- 외부 읽기: 고정 IDF SDK와 제조사 source 폴더만 별도 허용. backup 폴더는 제외.
- 쓰기: wrapper의 `--workspace`가 지정한 해당 run checkout 하나만 write_file 허용.
  runner는 실제 manifest checkout으로 예상 규칙을 계산해 불일치 시 시작 전에 차단한다.
  user home/root 등 광범위 경로는 wrapper에서도 거부한다. OS 격리 보장은 아니다.

실제 CLI는 작업 폴더의 native 쓰기도 별도 규칙 없이는 거부했다. 실패한 최초 workflow
smoke를 보존하고, 사용자에게 승인받은 파일 생성 범위에 맞는 checkout 한정 규칙을
새 fixture 실행에 적용했다. 거부된 세션에서 대체 명령으로 우회하지 않았다.

## 검증

전체 100개 회귀 시험 통과. 명령 허용/비허용 사례, SDK 외 경로 거부,
다른 checkout을 지정했을 때의 runner scope 검증 실패와 전역 복구를 포함한다.

실제 CLI의 별도 `agy-workflow-smoke-20260926-v2` 실행은 native note.txt 쓰기,
New-Item, Test-Path, Get-Content, IDF 5.3.2 버전·target·실제 binary 빌드,
생성된 binary와 파일을 확인하는 unittest 1개, SDK/제조사 source 읽기를 통과했다.
global settings/instructions/hooks 원본 복구도 byte 비교로 확인했다.
[실측과 hash](agy-workflow-smoke-20260926.json)를 보존한다. 이는 환경 시험이며 제품 증거가 아니다.
smoke는 별도 대화·별도 fixture 프로젝트이고 제품 prompt나 과거 제품 구현을 사용하지 않는다.
provider cache 격리는 주장하지 않으며 smoke 사용량도 제품 run과 분리한다.

profile의 정적 정책 fingerprint는 정렬·압축한 JSON의 semantic SHA-256
`df69d9d5ff7a66fa691e39f5c3ed005a330b90b0209838af71c29f4eb51d128b`다.
실제 byte hash와 checkout 경로를 포함한 effective settings hash는 wrapper와 receipt에
별도로 기록한다. policy JSON은 LF로 고정해 checkout의 줄바꿈 차이도 제거한다.

새 candidate: `agy-gemini-3.8-flash-workflow.candidate.json`.
실행에는 새 frozen baseline, profile-bound receipt, `--workspace <run>/checkout`을 쓴다.
진행 중 정책을 바꾸거나 후속 구현 지시를 보내지 않는다.
