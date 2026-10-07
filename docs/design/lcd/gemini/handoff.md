# Gemini LCD UX/UI Candidates A/B/C Handoff & Embedded Engineering Specification

## 1. 개요 및 후보 요약 (Executive Summary)

본 문서는 Waveshare ESP32-S3 3.16" LCD (ST7701 Controller, 820×320 가로 해상도, RGB565) 환경을 위한 Gemini LCD GUI 후보 A, B, C의 디자인 스펙, 정보 계층 구조, 상태 전이 규칙, 그리고 펌웨어(Sol) 구현자를 위한 하드웨어 렌더링 핸드오프 규격을 정의합니다.

모든 시안은 순수 오프라인 단일 HTML/CSS/Vanilla JS로 작성되었으며, 외부 웹폰트나 CDN 의존성 없이 즉시 브라우저에서 인터랙티브하게 검증 가능합니다.

---

## 2. 후보별 디자인 방향 및 비교 (Candidate Comparison)

| 구분 | 후보 A: Telemetry Matrix (gemini-a) | 후보 B: Swiss Studio Meter (gemini-b) | 후보 C: Industrial Field Gauge (gemini-c) |
|---|---|---|---|
| **디자인 콘셉트** | 고밀도 사이버네틱 텔레메트리 매트릭스 (Dark HUD) | 미니멀리즘 스위스 그리드 에디토리얼 (Warm Paper) | 러기드 인더스트리얼 계측기 (Amber Monospace) |
| **톤 & 매너** | 테크니컬, 정밀 제어, 엔지니어링 콕핏 | 차분함, 고대비 가독성, 정갈한 스튜디오 | 견고함, 아날로그 계측기, 즉각적인 시인성 |
| **배경색 / 메인색** | `#05080c` / `#38bdf8` (Cyan Neon) | `#f5f4ef` (Warm Cream) / `#18181b` (Ink) | `#0d0e10` / `#f59e0b` (Amber Orange) |
| **정보 우선순위** | 5h Quota 게이지와 세션 토큰 그리드가 동등하게 공존 | 대형 5h Quota 숫자가 압도하고, 우측에 세션 명세가 텍스트 중심 배치 | 3개 구획(5h 게이지, 주간 게이지, 토큰 리스트)이 명확한 물리적 프레임으로 분할 |
| **게이지 스타일** | 20-세그먼트 하이테크 LED 바 | 매끄러운 단일 솔리드 트랙 바 | 15-블록 인더스트리얼 세그먼트 블록 |
| **장점** | 한눈에 모든 세부 수치(캐시, 리즈닝, 소스시간 등)를 직관적으로 파악 가능 | 빛 반사가 적은 밝은 실내 조명 환경에서 눈의 피로도 최저, 미적 완성도 최고 | 야간 또는 어두운 데스크 환경에서 눈부심 방지 및 레트로 계측기 감성 극대화 |
| **단점 / 트레이드오프** | 정보 밀도가 높아 폰트 크기가 다소 오밀조밀함 | 밝은 배경으로 인해 ST7701 LCD 백라이트 전력 소모가 다크 테마 대비 약간 높음 | 모노스페이스 특성상 글자 너비가 넓어 텍스트 배치가 엄격히 제한됨 |

---

## 3. 공통 제품 의미 및 데이터 격리 규칙 (Semantics & Isolation)

1. **Quota vs Session 완전 격리:**
   - 5시간 롤링 윈도우(`used 42%`, `remaining 58%`, resets `18:20:00Z`)와 주간 윈도우(`used 18%`, `remaining 82%`)는 계정 단위의 Rate Limit입니다.
   - Session 토큰(`input 124,800`, `output 16,400`, `cached 89,600`, `reasoning 2,300`, `source total 141,200`)은 로컬 프로세스의 누적 스트림 측정값입니다.
   - **절대 세션 토큰을 Quota remaining에서 차감하거나, 세션 토큰의 백분율 잔여량을 임의로 계산하여 표시하지 않습니다.** (세션의 limit/remaining은 `UNKNOWN`으로 명시).
2. **글로벌 리셋(codex-resets.com):**
   - 글로벌 리셋 화면(BOOT 2번 화면)은 플랫폼 전체의 공용 리프레시 시각(`10:00:00Z`, 경과 `7h 10m`)만을 표시하며, 개인의 5시간 쿼터 리셋 시각과 혼동되지 않도록 출처를 명확히 고지합니다.
3. **Synthetic Provenance 명시:**
   - 시안 내 모든 데이터는 비식별 합성 데이터(Synthetic reference time: `2026-10-07T17:10:00Z`)임을 화면 하단 상태줄에 명시합니다.

---

## 4. BOOT 버튼 순환 네비게이션 (Screen State Machine)

ST7701 보드의 물리 `BOOT` 버튼(GPIO0, Active-Low)을 누를 때마다 화면이 아래 순서로 순환 전환됩니다:

```text
[화면 1: USAGE (사용량 & 세션)] 
       │ (BOOT 클릭)
       ▼
[화면 2: GLOBAL RESET (글로벌 리셋 현황)]
       │ (BOOT 클릭)
       ▼
[화면 3: STATUS (하드웨어/링크/진단)]
       │ (BOOT 클릭)
       └───► [화면 1: USAGE] 로 순환
```

- 각 HTML 시안 상단의 `🔘 PRESS BOOT [GPIO0] (Cycle Screen)` 버튼을 클릭하여 실제 순환 전환 동작을 완벽히 검증할 수 있습니다.

---

## 5. 데이터 상태 머신 및 결함 대응 (State Degradation Matrix)

외부 시뮬레이터 실렉터를 통해 검증 가능한 7가지 상태 동작 규격:

| 상태 (State) | 표시 동작 및 화면 반응 | 값 처리 규칙 |
|---|---|---|
| **Normal** | 녹색/청색 정상 뱃지, 신선한 데이터 표시 | 기준 합성 데이터 정상 렌더링 (`stat-src-age: 0s`) |
| **Source Stale** | 황색 경고 뱃지 + "SOURCE STALE: TOKEN TIMESTAMP > 5M" 경고 띠 | 기존에 관측된 수치를 유지하며 신선도 시간만 증가 (`384s STALE`) |
| **Disconnected** | 적색 경고 뱃지 + "LINK DISCONNECTED: USB TIMEOUT" 경고 띠 | 연결 단절 시 직전 정상 프레임(Last-Good) 수치를 화면에 유지 |
| **Unknown / Null** | 정보 띠 + 미지원 필드는 `--` 기호로 표시 | 게이지 바는 0% 비움, 수치 영역은 `--` 표기 (임의 0 추정 금지) |
| **Error / Last-Good**| 적색 알림 + "ERROR: CHECKSUM FAULT, LAST-GOOD RETAINED" | 오류 발생 시 안전하게 캐시된 직전 정상 스냅샷 값으로 폴백 |
| **Waiting** | 회색 뱃지 + "INITIALIZING: WAITING FOR FIRST CDM PACKET" | 부팅 초기 수신 대기 상태 (`...` 로 표기) |
| **Recovery** | 청색 안내 + "LINK RESTORED: CRC VALIDATED, REFRESHING" | 통신 복구 즉시 최신 유효 프레임으로 화면 재갱신 |

---

## 6. 임베디드 펌웨어(Sol) 구현 핸드오프 규격

### 6.1 디스플레이 물리 사양
- **컨트롤러:** ST7701 RGB 인터페이스 (DE, PCLK, VSYNC, HSYNC)
- **해상도:** 820 × 320 픽셀 (가로 모드)
- **색상 포맷:** RGB565 (16-bit, 픽셀당 2바이트)
- **프레임버퍼 크기:** $820 \times 320 \times 2 = 524,800$ 바이트 (ESP32-S3 PSRAM 80MHz Octal 영역에 할당)
- **백라이트 제어:** GPIO6, Active-Low PWM (duty = 255 - 밝기)

### 6.2 RGB565 컬러 매핑 테이블

| 색상 명칭 | CSS Hex | RGB888 (R, G, B) | RGB565 Hex | 주 용도 |
|---|---|---|---|---|
| **Candidate A (HUD)** | | | | |
| Background | `#05080c` | (5, 8, 12) | `0x0841` | LCD 전체 바탕 |
| Cyan Accent | `#38bdf8` | (56, 189, 248) | `0x3DF7` | 쿼터 수치, 세션 강조 |
| Panel Primary | `#0284c7` | (2, 132, 199) | `0x0438` | 메인 패널 테두리, 게이지 필 |
| Text Muted | `#64748b` | (100, 116, 139) | `0x63B1` | 단위 라벨, 경계선 |
| Text White | `#f0f6fc` | (240, 246, 252) | `0xF7BE` | 대형 핵심 숫자 |
| **Candidate B (Swiss)** | | | | |
| Paper BG | `#f5f4ef` | (245, 244, 239) | `0xF7BE` | 따뜻한 크림 배경 |
| Charcoal Ink | `#18181b` | (24, 24, 27) | `0x18C3` | 텍스트, 게이지, 메인 보더 |
| Gray Border | `#d4d4d8` | (212, 212, 216) | `0xD6BA` | 구분선 |
| Blue Highlight | `#0284c7` | (2, 132, 199) | `0x0438` | 캐시 토큰 강조 |
| **Candidate C (Field)** | | | | |
| Charcoal Case | `#0d0e10` | (13, 14, 16) | `0x0862` | 계측기 바탕 |
| Amber Primary | `#f59e0b` | (245, 158, 11) | `0xFD41` | 게이지 테두리, 헤더 |
| Amber Glow | `#fbbf24` | (251, 191, 36) | `0xFDE4` | 대형 계측 숫자 |
| Border Gray | `#36393f` | (54, 57, 63) | `0x39E7` | 내부 구획선 |

### 6.3 폰트 렌더링 및 래스터 비트맵 메모리 예산
펌웨어에서는 복잡한 벡터 폰트 엔진(FreeType) 대신 Flash ROM에 저장된 고정 크기 ASCII 비트맵 폰트를 사용할 것을 권장합니다:
1. **대형 숫자 폰트 (38px ~ 54px):**
   - 필요 글리프: `0-9`, `%`, `.`, `,`, `:`, `-` (총 16개 글리프)
   - 1글리프 크기: $38 \times 54$ 비트 $\approx 256$ 바이트
   - 16글리프 총 메모리: 약 **4.1 KB Flash ROM**
2. **중형 헤더 폰트 (16px ~ 20px):**
   - 필요 글리프: 대문자 알파벳 + 숫자 (약 40개 글리프)
   - 총 메모리: 약 **3.2 KB Flash ROM**
3. **소형 본문 폰트 (8px ~ 12px):**
   - 표준 기본 ASCII 128자 폰트 ROM (크기: 약 **1.5 KB**)

### 6.4 부분 재그리기 (Dirty Rect) 최적화 영역 좌표
ST7701의 화면 깜빡임 방지 및 버스 대역폭 절약을 위해 전체 화면 대신 변경된 구역만 부분 블릿(Blit)합니다:

```text
(0,0) ┌────────────────────────────────────────────────────────┐
      │  상단 시스템 바 (고정 영역) : [0, 0, 820, 28]             │
      ├───────────────────────────┬────────────────────────────┤
      │                           │                            │
      │  5h Quota Dirty Rect      │  Session Ledger Dirty Rect │
      │  [14, 38, 420, 120]       │  [448, 38, 358, 240]       │
      │                           │                            │
      │  Weekly Quota Dirty Rect  │  (토큰 카운트 갱신 시        │
      │  [14, 168, 420, 110]      │   이 구역만 DMA 전송)      │
      │                           │                            │
      ├───────────────────────────┴────────────────────────────┤
      │  하단 상태 바 (고정 영역) : [0, 296, 820, 24]            │
(0,320) └────────────────────────────────────────────────────────┘
```
- 토큰 증가 시: 우측 영역(`[448, 38, 358, 240]`, 약 85,920 픽셀 = 171KB DMA)만 전송하여 60fps 갱신 가능.
- 쿼터 갱신 시: 좌측 쿼터 영역(`[14, 38, 420, 120]`, 약 100KB DMA)만 전송.
