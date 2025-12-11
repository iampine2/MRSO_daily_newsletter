# MRSO Daily Newsletter

게임 뉴스 자동 수집 및 뉴스레터 생성 시스템

## 🚀 기능

- **자동 크롤링**: IGN, GameSpot, Gamelook에서 24시간 내 게임 뉴스 수집
- **2단계 필터링**: 
  - 1단계: 원문으로 게임 관련성 & 중요도 빠른 평가 (토큰 절약)
  - 2단계: 필터 통과한 기사만 번역 & 요약 (고품질 처리)
- **AI 분석**: Claude API로 번역, 요약, 카테고리 분류, 일일 트렌드 분석
- **HTML 뉴스레터**: 모바일 & 새 Outlook 최적화 디자인
- **자동 실행**: GitHub Actions로 매일 오전 9시 자동 실행

## 📦 설치

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하세요:

```bash
# .env 파일 생성
# Claude API Key (https://console.anthropic.com/)
CLAUDE_API_KEY=your-claude-api-key-here

# Webhook URL (Make.com)
WEBHOOK_URL=https://hook.us2.make.com/x66njlvg1dx6jxethzuy4n92w4xrgua5
```

**중요**: `.env` 파일은 Git에 커밋되지 않습니다! (`.gitignore`에 포함됨)

### 3. Chrome & ChromeDriver 설치

- **Windows/Mac**: Chrome 브라우저만 설치하면 Selenium이 자동으로 ChromeDriver를 관리합니다.
- **Linux (GitHub Actions)**: Workflow에서 자동 설치됩니다.

## 🎮 사용법

### 로컬 실행

```bash
python main.py
```

실행 결과:
- `collected_articles.json`: 수집된 기사 데이터
- `daily_newsletter.html`: 생성된 뉴스레터 HTML

### GitHub Actions (자동 실행)

1. GitHub Repository Settings → Secrets and variables → Actions
2. 다음 환경변수 추가:
   - `CLAUDE_API_KEY`: Claude API 키
   - `WEBHOOK_URL`: Make.com 웹훅 URL

3. 매일 오전 9시(KST) 자동 실행됩니다.

## 📊 2단계 필터링 시스템

### 왜 2단계인가?

기존에는 모든 기사를 번역 → 요약 → 분석 → 필터링하여 **토큰 낭비**가 심했습니다.

### 개선된 방식

```
수집된 기사 (100개)
    ↓
[1단계] 빠른 필터링 (원문 평가, ~150 토큰/기사)
    ├─ 통과: 30개 (관련성 ≥ 0.5, 중요도 ≥ 0.4)
    └─ 제외: 70개 💰 토큰 절약!
    ↓
[2단계] 번역 & 요약 (30개만, ~1500 토큰/기사)
    └─ 고품질 번역 + 요약 + 카테고리
    ↓
최종 결과 (30개)
```

### 예상 절감 효과

- **기존**: 100개 × 1500 토큰 = 150,000 토큰 (~$0.45)
- **개선**: 100개 × 150 + 30개 × 1500 = 60,000 토큰 (~$0.18)
- **절감**: **60% 토큰 절약!** 💰

## 📁 프로젝트 구조

```
MRSO_daily_newsletter/
├── main.py                    # 메인 크롤링 스크립트
├── generate_html.py           # HTML 뉴스레터 생성
├── requirements.txt           # Python 패키지 목록
├── .env                       # 환경변수 (로컬용, Git 제외)
├── .gitignore                 # Git 제외 파일 목록
├── collected_articles.json    # 수집된 기사 (자동 생성)
├── daily_newsletter.html      # 생성된 뉴스레터 (자동 생성)
└── .github/
    └── workflows/
        └── daily-crawler.yml  # GitHub Actions 워크플로우
```

## 🔧 주요 함수

### `quick_filter(title, content)`
- **목적**: 1단계 빠른 필터링
- **입력**: 원문 제목 + 본문 (처음 500자)
- **출력**: `game_relevance`, `importance`, `should_process`
- **모델**: Claude Sonnet 4 (저렴)
- **토큰**: ~150 토큰

### `translate_and_summarize(title, content)`
- **목적**: 2단계 번역 & 요약
- **입력**: 필터 통과한 기사
- **출력**: `title_kr`, `content_summary_kr`, `category`
- **모델**: Claude Sonnet 4.5 (고품질)
- **토큰**: ~1500 토큰

### `generate_daily_summary(articles)`
- **목적**: AI 일일 트렌드 분석
- **입력**: 수집된 기사 목록
- **출력**: 4개 불릿 포인트 요약

## 📝 카테고리

- **규제 & 이슈**: 게임 산업의 규제, 문제점, 논란
- **게임 출시 & 발표**: 새로운 게임 출시, 개발 발표
- **매출 & 성과**: 게임 판매 실적, 수익, 비즈니스 전략
- **업데이트 & 패치**: 게임 패치, 기능 업데이트
- **IP & 콜라보**: 게임 IP 관련 뉴스, 협업, 미디어 확장
- **커뮤니티 & 이벤트**: 게임 이벤트, 팬 행사, 프로모션

## 🎯 필터링 기준

### 게임 관련성 (game_relevance)
- **1.0**: 게임 개발, 출시, 업데이트
- **0.5-0.9**: 게임 IP 미디어 확장 (영화, 드라마)
- **0.0-0.4**: 게임 무관 (제외)

### 중요도 (importance)
- **0.7-1.0**: 산업 보고서, 규제, 전략 변화
- **0.4-0.7**: 신작 출시, 메이저 업데이트
- **0.2-0.4**: 마이너 패치, 가이드 (제외)
- **0.0-0.2**: 세일, 할인, 게이밍 기어 (제외)

**필터 통과 조건**: `game_relevance >= 0.5` **AND** `importance >= 0.4`

## 🌐 데이터 소스

- **IGN** (https://www.ign.com/news) - 북미 게임 뉴스
- **GameSpot** (https://www.gamespot.com/news) - 북미 게임 뉴스
- **Gamelook** (http://www.gamelook.com.cn/) - 중국 게임 뉴스

## 📧 뉴스레터 디자인

- **HOT TREND**: 상위 5개 기사 (댓글 수 기준)
- **AI SUMMARY**: 일일 게임 산업 트렌드 (4개 불릿)
- **카테고리별 섹션**: 규제, 출시, 매출, 업데이트, IP, 커뮤니티
- **반응형 디자인**: 모바일 & 새 Outlook 최적화

## 📄 라이선스

© 2025 MRSO Daily Global News

---

**문의**: iampine2@github.com
