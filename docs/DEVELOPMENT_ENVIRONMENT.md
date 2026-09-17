# Windows 개발 환경

## 기준 환경

2026-09-11 현재 Version 2인 Waveshare ESP32-S3-LCD-3.16 개발은 다음 환경을
기준으로 한다.

| 항목 | 고정값 |
|---|---|
| 운영체제 | Windows |
| 프레임워크 | ESP-IDF v5.3.2 |
| 설치 관리자 | Espressif Installation Manager CLI 0.19.0 |
| 대상 SoC | ESP32-S3 |
| 기본 포트 | COM3 |
| ESP-IDF 설치 경로 | `C:\Espressif\v5.3.2\esp-idf` |
| 도구 설치 경로 | `C:\Espressif\tools` |
| Python | 3.11.15 |
| CMake | 3.30.2 |
| Ninja | 1.12.1 |
| Xtensa GCC | 13.2.0 |

ESP-IDF v5.3.2는 출고 `RGB_Demo`의 부팅 로그에서 관찰된
`v5.3.2-dirty`와 같은 릴리스 계열이므로 첫 bring-up 기준으로 선택했다.

## 설치

새 Windows PC에서는 PowerShell에서 EIM CLI를 설치한 후 ESP-IDF를 설치한다.

```powershell
winget install --id Espressif.EIM-CLI --exact `
  --accept-package-agreements --accept-source-agreements

eim install -p C:\Espressif -i v5.3.2 -t esp32s3 -n true -a true `
  --idf-features pytests --do-not-track true `
  --config-file-save-path C:\Espressif\eim-v5.3.2.toml
```

설치 뒤 저장소 루트에서 환경을 현재 PowerShell 세션에 활성화한다. 앞의 점과
공백을 포함해 dot-source 방식으로 실행해야 한다.

```powershell
. .\scripts\activate-idf.ps1
idf.py --version
```

## 한글 Windows 경로 제약

ESP-IDF v5.3.2 Windows 도구와 EIM에 포함된 ccache 4.10.2는 한글이 포함된
프로젝트 또는 빌드 경로에서 각각 인코딩 오류와 문자 변환 오류를 일으켰다.
따라서 다음 두 조건을 기준으로 한다.

1. ESP-IDF, 임시 파일과 빌드 경로는 `C:\Espressif` 아래 ASCII 경로를 사용한다.
2. `IDF_CCACHE_ENABLE=0`으로 ccache를 비활성화한다.

현재 Orca 작업공간에는 다음 ASCII junction을 만들었다.

```text
C:\Espressif\projects\codex-desk-meter-main-2
  -> C:\path\to\workspaces\codex-desk-meter\main-2
```

위 junction은 historical `main-2`/실험 worktree용이다. 정식 문서와 새 baseline의
기준은 별도 `main` worktree이며, worktree 경로와 Git branch 이름을 혼동하지
않는다. 실행 전 gate가 열리기 전에는 이 경로에 agent를 시작하지 않는다.

새 clone이나 worktree는 처음부터 `C:\src\codex-desk-meter`처럼 ASCII 경로에
두는 방법을 권장한다. 현재 작업공간에서 빌드할 때는 위 junction 경로로
이동해서 `idf.py`를 실행한다.

## ASCII junction 도구 경로 (2026-09-18 수리)

EIM 프로필(`Microsoft.v5.3.2.PowerShell_profile.ps1`)이 한글 사용자명 경로에서
파싱 오류를 내고, Rust 기반 xtensa wrapper가 한글 경로에서 패닉한다. 수리 내용:

1. `idf_tools.py install` + `install-python-env`로 부족분을 사용자
   `.espressif`에 보완 (UTF-8·ASCII TEMP 필수).
2. ASCII junction 생성: `C:\Espressif\user-tools` →
   사용자 `.espressif`. 모든 경로 문자열이 ASCII가 되어 wrapper 패닉 해소.
3. 환경 변수: `IDF_PATH=C:\Espressif\v5.3.2\esp-idf`,
   `IDF_TOOLS_PATH=C:\Espressif\user-tools`, `IDF_CCACHE_ENABLE=0`,
   `PYTHONUTF8=1`, `TEMP/TMP=C:\Espressif\tmp`.
4. `idf_tools.py export` 출력을 파일 경유(UTF-8)로 읽어 PATH에 반영한다.
   콘솔 직접 파이프는 한글 경로에서 불안정하다.
5. 위 순서로 `idf.py --version` → `ESP-IDF v5.3.2`,
   `hello-world` 전체 빌드 성공을 실측했다 (산출물: `hello_world.bin`,
   `bootloader.bin`).

`scripts/activate-idf.ps1`은 이제 `C:\Espressif\user-tools`가 있으면 해당
설치의 Python 환경과 `idf_tools.py export --format key-value`를 사용한다.
환경 값을 key/value로 적용하며 EIM 프로필을 실행하지 않는다. `-ToolsRoot`로
동일 구조의 다른 설치를 지정할 수 있다. 해당 경로가 없으면 기존 EIM 활성화를
사용하며, 어느 경로든 Python 의존성 및 실제 IDF 버전 확인이 실패하면 중단한다.

## 검증 결과

다음 항목을 실제로 확인했다.

- `idf.py --version`: `ESP-IDF v5.3.2`
- `esptool.py --chip esp32s3 --port COM3 chip_id`: ESP32-S3 rev v0.2 통신 성공
- 공식 `hello_world` 예제를 ESP32-S3 대상으로 구성하고 전체 빌드 성공
- 생성 파일: `hello_world.bin`, `bootloader.bin`, `partition-table.bin`

검증용 예제는 `C:\Espressif\smoke-tests\hello-world-v5.3.2`에 있으며 빌드
출력도 같은 ASCII 경로 아래 `build-ascii`에 두었다. 이 검증에서는 RAM stub만
실행하고 하드 리셋했으며 플래시 쓰기나 삭제는 하지 않았다.

## 일상 명령

펌웨어 프로젝트가 승인된 실험 checkout에 추가된 뒤 다음 흐름을 사용한다.
현재 `main`의 계획 단계에서는 아래 `flash monitor`를 실행하지 않는다.

```powershell
. .\scripts\activate-idf.ps1
Set-Location C:\Espressif\projects\codex-desk-meter-main-2
idf.py set-target esp32s3
idf.py build
idf.py -p COM3 flash monitor
```

마지막 `flash monitor`는 펌웨어를 실제로 덮어쓴다. 출고 펌웨어 백업 정책과
업로드 대상 이미지를 확정하기 전에는 실행하지 않는다. COM3는 한 번에 한
운영자만 점유하며, agent가 임의로 flash하지 않는다.

## Waveshare 제조사 예제

공식 Demo ZIP을 받아 ESP-IDF 예제를 빌드하려면 다음 스크립트를 사용한다.

```powershell
.\scripts\fetch-waveshare-demo.ps1
.\scripts\build-waveshare-example.ps1 -Example factory
```

`factory`는 16MB Flash 설정의 `09_FactoryProgram`이고, LCD 그래픽 경로만
확인하려면 `-Example lvgl9`로 `08_LVGL_V9_Test`를 빌드할 수 있다. 두 예제의
실제 결과와 08번의 8MB 설정 주의사항은
[제조사 예제 빌드 기록](hardware/waveshare-manufacturer-example.md)을
참조한다.

## 현재 상태와 다음 단계

다음 bring-up 항목은 완료됐다.

- Waveshare 공식 Demo ZIP 확보와 ESP-IDF 예제 빌드
- 16MiB 출고 플래시 백업 및 SHA-256 검증
- `09_FactoryProgram` COM3 업로드와 시리얼 부팅 확인
- LCD, BOOT 입력과 RST 재열거 동작 확인

현재 저장소에는 제품 펌웨어 프로젝트가 없으므로 `idf.py build`를 실행하려면
먼저 기준 에이전트가 `CMakeLists.txt`와 `main/`을 생성해야 한다. 구현·실험
준비는 [제품 계약](PRODUCT_CONTRACT.md), [readiness gate](experiments/benchmark-readiness.md)와
[에이전트 실험 프로토콜](experiments/agent-experiment-protocol.md)을 따른다.
