# 하드웨어 자율 기능 선택 보고서 (보정 최종본)

- **실행 ID (Run ID)**: `20260911-antigravity-cli-gemini-3-8-flash-high-r01`
- **현재 브랜치**: `experiment/antigravity/cli/gemini-3-8-flash-high`
  - *(참고: 작업 폴더 경로는 `main-2`이나 Git 브랜치는 `experiment/antigravity/cli/gemini-3-8-flash-high`임)*
- **기준 커밋 (Base Commit)**: `c0ba9e2d812b5e193784418ff993af454019d3c7`
  - *(주의: 기준 커밋이며 구현 커밋이 아닙니다. 구현 파일들은 uncommitted 상태로 보존되어 있습니다)*
- **대상 보드**: Waveshare ESP32-S3-LCD-3.16 (ESP32-S3-WROOM-1-N16R8, 16MB Flash, 8MB Octal PSRAM)
- **개발 프레임워크**: ESP-IDF v5.3.2
- **실행 분류**: `manual pilot; invalid for cross-agent quantitative comparison`

---

## 1. 하드웨어 기능 후보 3개 평가

제조사 공식 예제(`09_FactoryProgram`) 및 하드웨어 사양을 기반으로 온보드 자원을 사용하는 3개 기능 후보를 평가하였습니다.

### 후보 1: IMU 기반 책상 탭 및 제스처 인터랙션 [선택]
- **식별자**: `imu-gesture-interaction`
- **사용 하드웨어 자원**: 온보드 QMI8658 6축 IMU (I2C 주소 `0x6B`, SCL `GPIO 7`, SDA `GPIO 15`, WHO_AM_I `0x05`)
- **사용자 가치**:
  - 320x820 세로형 초슬림 디스플레이는 거치 면적이 좁아 기기 측면/후면의 BOOT 버튼을 직접 누르면 기기가 밀리거나 거치 각도가 흐트러질 수 있습니다.
  - 책상 상판을 가볍게 두 번 두드리는 **책상 더블 탭(Desk Double-Tap)**으로 화면을 전환(C8)하고, 기기를 가볍게 흔드는 **셰이크(Shake)** 제스처로 즉시 수동 갱신을 수행할 수 있는 탁상 편의성을 제공합니다.
- **구현 비용**: 중간 (하드웨어 I2C 제어와 순수 detector C 알고리즘 분리, 중력 벡터 배제, 고역 통과 필터, 타이핑 노이즈 억제 및 탭 간격 80~550ms 윈도우 판정 알고리즘, 메인 루프 polling 처리).
- **위험 요소 및 제한사항**:
  - 일상적인 키보드 타이핑 진동으로 인한 오작동(False Positive) 가능성.
  - 실물 보드 미검증 상태이므로 센서 노이즈 및 물리 진동 특성에 따른 실물 보정이 필요함.
- **검증 계획**: 순수 C detector 호스트 테스트(`test_imu_detector.c`), Python 시뮬레이션 검증, ESP-IDF 통합 빌드 검증 및 실물 보드 제스처 검증 계획 수립.

### 후보 2: PCF85063 RTC 기반 오프라인 시간 유지 [탈락]
- **식별자**: `rtc-power-loss-timekeeping`
- **사용 하드웨어 자원**: 온보드 PCF85063 I2C RTC (I2C 주소 `0x51`, SCL `GPIO 7`, SDA `GPIO 15`)
- **사용자 가치**: 전원 재인가 또는 장시간 Wi-Fi 단절 시에도 RTC 시간을 유지하여 마지막 데이터의 Stale(300초 경과) 여부를 계산.
- **구현 비용**: 낮음 (I2C 레지스터 읽기/쓰기 및 POSIX time 연동).
- **탈락 이유**:
  - Codex Desk Meter는 상시 책상 위 USB-C 전원 인가 기기이며, 코인셀 백업 배터리가 미장착된 경우 전원 차단 시 시간이 소실됩니다.
  - 고정 fixture 및 네트워크 복구 환경에서 단일 타이머 및 SNTP로도 C3/C7 Stale 요구사항을 충족할 수 있어, 추가적인 사용자 경험 개선 효과가 상대적으로 제한적입니다.

### 후보 3: 배터리 전압 ADC 모니터링 및 저전력 알림 [탈락]
- **식별자**: `battery-adc-power-monitor`
- **사용 하드웨어 자원**: ESP32-S3 내장 ADC (GPIO 1 / 배터리 분압 회로)
- **사용자 가치**: 배터리 잔량을 대시보드에 표시하고 저전압 경고 제공.
- **구현 비용**: 중간 (ADC 원시값 칼리브레이션, 리튬 배터리 방전 곡선 매핑, UI 잔량 표시).
- **탈락 이유**:
  - 320x820 대화면 RGB LCD 백라이트를 상시 구동하는 책상 거치형 데스크 미터 특성상 상시 5V USB-C 공급이 표준 운용 환경입니다.
  - 배터리 구동은 주 사용 시나리오가 아니며 데스크 위 인터랙션 가치가 낮아 우선순위에서 제외하였습니다.

---

## 2. 하드웨어 구성 및 제조사 예제 대조 검토

제조사 `09_FactoryProgram` 예제와 본 구현의 하드웨어 구성을 대조한 결과는 다음과 같습니다.

1. **디스플레이 및 버스 핀 매핑**:
   - 해상도: 320 × 820, ST7701 컨트롤러, 16-bit RGB565 병렬 버스.
   - 제어 신호: DE `GPIO 40`, PCLK `GPIO 41`, VSYNC `GPIO 39`, HSYNC `GPIO 38`, RESET `GPIO 16`.
   - 데이터 신호 (BGR 순서): B0~B4 (`GPIO 21, 5, 45, 48, 47`), G0~G5 (`GPIO 14, 13, 12, 11, 10, 9`), R0~R4 (`GPIO 17, 46, 3, 8, 18`).
   - 제조사 예제와 완벽히 일치함을 확인.
2. **I2C 버스 핀 매핑 및 센서 주소**:
   - SCL: `GPIO 7`, SDA: `GPIO 15`.
   - QMI8658 6축 IMU: I2C 주소 `0x6B`, `WHO_AM_I` 레지스터(`0x00`) 기대값 `0x05`.
   - PCF85063 RTC: I2C 주소 `0x51`.
3. **GPIO 0 공유 (LCD 3-wire SPI CS vs BOOT 버튼) 및 초기화 순서**:
   - **하드웨어 설계**: GPIO 0은 LCD 3-wire SPI의 CS 라인이자 물리 BOOT 버튼으로 공유되어 있습니다.
   - **초기화 순서**: 본 구현에서는 제조사 권장 패턴에 따라 `display_ui_init()`을 먼저 호출하여 3-wire SPI를 통해 ST7701 레지스터 초기화를 완료한 후, `board_input_init()`에서 GPIO 0을 버튼 입력 풀업 모드로 전환합니다.
   - **런타임 영향 및 위험**: ST7701은 초기화 완료 후 RGB 병렬 인터페이스로만 프레임 버퍼를 수신하므로, 런타임에 SPI CS를 사용하지 않아 버튼 입력과 버스 충돌이 발생하지 않습니다. 단, 버튼을 누를 때 CS 라인이 물리적으로 GND로 당겨지므로 하드웨어 회로 노이즈나 신호 간섭 가능성에 대해서는 **반드시 실물 보드 검증이 필요**합니다.
4. **PSRAM 및 프레임버퍼 할당**:
   - ESP32-S3 Octal PSRAM 8MB를 활용하여 320x820x2바이트 전체 화면 버퍼를 SPIRAM(`MALLOC_CAP_SPIRAM`)에 할당.
   - RGB 패널 `num_fbs = 2`, `fb_in_psram = 1` 설정 적용.
5. **LCD 초기화 반환값 처리**:
   - 패널 생성 및 SPI 통신 실패 시 `ESP_LOGW` 경고 로그를 출력하며, 메모리 부족 외에는 시스템 충돌(panic) 없이 복구 가능한 구조로 작성됨.

---

## 3. 소프트웨어 아키텍처 및 테스트 소스 구성

1. **파서 모듈 및 테스트 어댑터**:
   - `components/meter/src/meter_parser.c`: 펌웨어용 production C 파서.
   - `tests/meter_test_adapter.c`: `meter_parser.c`를 직접 호출하는 **production-linked C 어댑터 소스** (현재 상태: source present, 호스트 C 컴파일러 부재로 실행은 `not_run`).
   - `tests/cJSON.c`, `tests/cJSON.h`: `meter_test_adapter.c`가 사용하는 cJSON 구현.
   - `tests/meter_test_adapter.py`: Python으로 구현된 **독립 reference adapter** (`evaluate-product.py` 연동용).
2. **IMU 제스처 모듈 및 테스트 소스**:
   - `components/imu_gesture/include/imu_detector.h`, `src/imu_detector.c`: 하드웨어 독립적인 순수 C detector 알고리즘.
   - `components/imu_gesture/include/imu_gesture.h`, `src/imu_gesture.c`: 타깃 ESP-IDF I2C 하드웨어 제어 레이어.
   - `tests/test_imu_detector.c`: 순수 C detector 호스트 단위 시험 소스 (`test_imu_gesture.c`의 구버전 의존성을 개선한 상위 대체 파일).
   - `tests/test_imu_gesture.py`: Python simulation reference test.
3. **실행 구조**:
   - `main/main.c` 메인 루프에서 50ms 주기로 `board_input_poll()` 및 `imu_gesture_poll_hardware()`를 호출하는 **polling 방식**.

---

## 4. 검증 결과 상세 구분

각 검증 항목의 상태와 근거를 명확히 구분합니다.

| 검증 항목 | 상태 (Status) | 근거 및 세부 내역 |
|---|:---:|---|
| **firmware build** | **PASS** | ESP-IDF v5.3.2 타깃 `esp32s3` 빌드 성공 (`codex_desk_meter.bin` 357,584 bytes 생성, 종료 코드 0). 순수 C detector 분리 반영 완료. |
| **Python reference adapter** | **PASS** | `evaluate-product.py --adapter-config adapter-config.json` 실행 결과 **29/29 PASS** (종료 코드 0). 주의: Python 독립 재구현 어댑터를 통한 검증임. |
| **production C parser host evaluation** | **not_run** | `meter_test_adapter.c` 소스는 준비되어 있으나, 호스트 환경(Windows)에 x86_64 네이티브 C 컴파일러 부재로 호스트 실행 불가. |
| **production C IMU detector host test** | **not_run** | `test_imu_detector.c` 소스는 준비되어 있으나, 호스트 네이티브 C 컴파일러 부재로 빌드/실행 불가 (`CommandNotFoundException`, 종료 코드 1). |
| **Python IMU simulation** | **PASS** | `tests/test_imu_gesture.py` reference simulation 5종 통과 (종료 코드 0). |
| **result contract validation** | **not_run** | 사유: runner-generated `run-manifest.json` 부재. `validate-experiment-result.py`는 `--result` 지정 시 `--manifest`가 필수이며, manifest는 운영자 관리 자산이므로 에이전트가 임의 생성하지 않음. (인수 없는 validator 실행은 예제 검증용임) |
| **hardware status** | **not_run** | COM3 플래시 및 실물 모니터링 미실행 (실험 프로토콜 준수). |
| **product pass** | **false** | 실물 하드웨어 검증 및 production C host 검증 미실행에 따른 제품 최종 미합격 상태. |

### C1~C8 계약 판정 요약 (보수적 분리 판정)

| 계약 항목 | 내용 | 펌웨어 빌드 | 호스트 검증 | 실물 검증 | 최종 판정 |
|---|---|:---:|:---:|:---:|:---:|
| **C1** | ESP-IDF 타깃 설정 및 빌드 | PASS | N/A | N/A | **PASS** |
| **C2** | 320x820 세로 ST7701 LCD 출력 | PASS | N/A | not_run | **not_run** |
| **C3** | 개인 사용량 5h/Weekly 정규화 | PASS | Python adapter PASS / C host not_run | not_run | **partial** |
| **C4** | 최근 글로벌 리셋 시각 표시 | PASS | Python adapter PASS / C host not_run | not_run | **partial** |
| **C5** | 24h/48h 리셋 전망 확률 표시 | PASS | Python adapter PASS / C host not_run | not_run | **partial** |
| **C6** | 독립 출처 분리 보존 | PASS | Python adapter PASS / C host not_run | not_run | **partial** |
| **C7** | 장애 내결함성 및 자동 복구 | PASS | Python adapter PASS / C host not_run | not_run | **partial** |
| **C8** | BOOT 버튼 및 화면 순환 | PASS | N/A | not_run | **not_run** |

- **종합 판정 문구**:
  > **“firmware build pass, host evaluation pass, hardware not run, product pass false”**

---

## 5. 남은 실물 검증 항목 (COM3 운영자 승인 후 수행 대상)

1. **C2 LCD 실물 패널 출력**:
   - 320 × 820 ST7701 3-wire SPI 초기화 및 RGB 병렬 인터페이스 출력 정상 동작 확인.
   - 대시보드 화면(사용량 게이지, 글로벌 리셋 일시, 전망치)의 잘림 및 색상 왜곡 여부 확인.
2. **C8 BOOT 버튼 입력 및 화면 순환**:
   - GPIO 0 물리 버튼 클릭 시 50ms 디바운스 및 0(대시보드) -> 1(리셋) -> 2(상태) 화면 순환 동작 확인.
3. **GPIO 0 신호 간섭 점검 (하드웨어 위험 항목)**:
   - LCD 3-wire SPI CS와 BOOT 버튼이 물리적으로 GPIO 0을 공유하므로, 런타임에 버튼을 누를 때 SPI 라인 접지(GND)에 따른 LCD 화면 노이즈나 하드웨어 오동작이 발생하는지 실측 확인.
4. **QMI8658 온보드 IMU 실물 제스처 검증**:
   - 실제 I2C 버스(`SCL GPIO7`, `SDA GPIO15`) 통신 및 `WHO_AM_I` (`0x05`) 응답 확인.
   - 책상 상판 재질에 따른 더블 탭 진동 감도 실측 및 기기 셰이크 시 수동 갱신 동작 확인.

---

## 6. 정식 벤치마크 비교 제외 사유

본 실행은 다음 운영 인프라 증거가 결여되어 있으므로, 타 에이전트와의 정식 정량 비교가 불가능한 **`manual pilot; invalid for cross-agent quantitative comparison`**으로 분류됩니다.

1. 운영 실행기가 생성한 공인 `run-manifest.json` 부재
2. 공식 검증된 `runner profile` 미적용
3. `sandbox receipt` 및 원본 명령 실행 추적 로그(`commands.jsonl`) 부재
4. 표준 측정 환경의 원시 표준 출력/에러(`raw stdout/stderr`) 로그 미수집
5. 검증 가능한 시작·종료 시각 및 정밀 wall-clock 시간 미측정
6. 토큰 소비량(`input`, `output`, `cached`, `reasoning`, `total`) 미제공 (임의 추정 없이 `null` 유지)
