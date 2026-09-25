# AGY 첫 pilot 권한 정책 — 2026-09-25

## 결정

사용자는 첫 `antigravity-cli / gemini-3.8-flash-medium` pilot의 도구 권한을 **필요한
명령만 사전 허용**하는 방식으로 선택했다. `--dangerously-skip-permissions`는 이
profile의 argv에 넣지 않는다. 이 결정은 도구 권한 방식의 선택이며 R10 실행 인가나
R4/R5 통과 판정은 아니다.

## 현재 근거와 제약

- 로컬 AGY CLI는 2026-09-25 재확인 시 1.2.11이다. 현재 전역
  `~/.gemini/antigravity-cli/settings.json`의 SHA-256은
  `A9E7B57B56BB0225448A7068F18264CA3056C5A3C0EE49114F37BF4292EE0D48`다.
- `permissions.allow`에는 `command(...)` 14개와 `unsandboxed(...)` 100개가 있다.
  `permissions.ask`와 `permissions.deny` 속성은 설정 파일에 없다. Windows에서
  설정되지 않은 명령의 기본 판정은 Ask다. 일부 기존 command 규칙은
  이전 checkout의 절대 경로를 가리킨다. 현재 목록만으로 새 checkout의 명령
  허용을 입증할 수 없다.
- `allowNonWorkspaceAccess=true`와 전역 `~/.gemini/GEMINI.md`가 존재한다. 첫
  값은 작업 공간 밖 접근 가능성을, 둘째는 공통 prompt 밖 지침 가능성을
  뜻하므로 profile의 reference 제한과 지침 범위를 별도로 검토한다.
- [공식 AGY headless 문서](https://www.antigravity.google/docs/cli/headless/)는 승인
  필요 도구가 비대화형 실행에서 거부돼도 프로세스가 exit 0일 수 있다고 설명한다.
  [공식 권한 문서](https://www.antigravity.google/docs/permissions/)에 따르면 CLI의
  규칙은 전역 settings에 있고 `deny > ask > allow` 순서로 적용된다. Windows
  PowerShell 명령은 단순 prefix 규칙만으로 매칭되지 않을 수 있다.

## 적용 전 점검과 고정 절차

1. 최종 baseline의 깨끗한 checkout, 실제 AGY argv, 실행 환경을 확정한다. 운영자 shell과
   runner 자식 프로세스에 `AGY_CLI_DISABLE_AUTO_UPDATE=true`를 설정하고, 실행 직전
   AGY 버전·실행 파일 hash를 재확인한다. 다른 프로세스의 공유 바이너리 갱신 가능성도
   별도 점검한다. 새
   checkout의 IDF 빌드·Python 검증·Git 확인에 필요한 **실제 명령 문자열**을
   수집한다. 목적과 인자가 확인되지 않은 명령을 통째로 허용하지 않는다.
2. 다른 AGY 세션이 없는 실험 창을 정하고 전역 settings 원본을 백업해 SHA-256을
   남긴다. 실험 창에는 기존 114개 allow 규칙을 그대로 상속하지 않고 pilot 전용
   허용 목록으로 좁힌다. 변경 전후 파일 hash와 diff를 별도 evidence로 보존하고
   pilot 종료 후 원본 복원 여부와 복원 hash를 기록한다.
3. 정확한 명령 또는 좁은 패턴만 허용한다. 특히 Windows shell wrapper의
   전체 명령줄 매칭을 확인한다. `command(*)`, 포괄적인 `powershell`/`python`
   허용, 전체 도구 자동 승인은 사용하지 않는다. 미등록 명령은 거부된 것으로
   기록하고 pilot 도중 즉흥적으로 허용 범위를 넓히지 않는다.
4. `agy --version`, `agy --help`, `agy models`, 설정·확장·전역 지침 inventory를
   다시 기록한다. profile의 `approval_policy`에는 의도한 effective mode를
   넣고, receipt에는 settings hash와 허용 규칙의 근거를 연결한다. `check`와
   receipt가 통과할 때까지 `prepare`를 하지 않는다.
5. R10 발효 뒤 첫 pilot에서 raw stdout/stderr와 `init.permission_mode`,
   `init.model`, tool error를 대조한다. soft denial 또는 예상 밖 명령이 있으면
   유효한 비교 결과로 승격하지 않는다. runner는 구조화된 permission/approval
   `tool_info.error.type`을 발견하면 실행 실패로 분류하지만, stderr에만 나타나는
   거부도 있을 수 있으므로 원본 로그를 별도로 검토한다. 필요한 정책 변경은 다음 날짜의 새
   profile·receipt·run에서 검토한다.

현재 정확한 명령 허용 목록과 effective 정책은 아직 정해지지 않았다. 따라서 이
문서는 적용 계획이며 R4=`not_ready`, R5=`blocked`를 유지한다. 기존 전역 설정은
이 문서 작성으로 변경되지 않았다.
