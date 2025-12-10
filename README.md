# MRSO Daily Newsletter Crawler

게임 뉴스 사이트(IGN, GameSpot, Gamelook)에서 24시간 이내 기사를 자동으로 수집하고 HTML 뉴스레터로 변환하는 크롤러입니다.

## 기능

- **자동 수집**: 매일 오전 9시(KST)에 자동으로 실행
- **다중 사이트 지원**: IGN, GameSpot, Gamelook
- **24시간 필터링**: 실행 시점 기준 24시간 이내 기사만 수집
- **AI 번역 & 요약**: Claude API를 사용한 한국어 번역 및 요약
- **카테고리 자동 분류**: 6개 카테고리로 자동 분류
- **게임 연관도 평가**: 0~1 스케일로 게임 관련성 평가
- **HTML 뉴스레터 생성**: 이메일 친화적인 HTML 포맷으로 변환
- **웹훅 전송**: Make.com으로 HTML 자동 전송
- **댓글 수 정렬**: 인기 기사 우선 (HOT TREND)

## 설치 및 실행

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 크롤러 실행
python main.py
```

### GitHub Actions 자동 실행

1. 이 저장소를 GitHub에 푸시
2. GitHub Actions가 자동으로 매일 오전 9시(KST)에 실행됩니다
3. 수동 실행: GitHub > Actions > Daily News Crawler > Run workflow

## 출력 형식

### collected_articles.json

```json
[
  {
    "title": "기사 제목 (원문)",
    "title_kr": "기사 제목 (한국어)",
    "url": "https://...",
    "date": "2025-12-09 15:21",
    "comments": 288,
    "thumbnail": "https://...",
    "body": "본문 내용...",
    "content_summary_kr": "명사형 종결어미로 작성된 요약",
    "category": "게임 출시 & 발표",
    "game_relevance": 1.0,
    "media": "IGN"
  }
]
```

### daily_newsletter.html

이메일 클라이언트(Outlook, Gmail 등)에 최적화된 HTML 뉴스레터:

- **HOT TREND 섹션**: 댓글 10개 이상, 최대 4개 기사
- **카테고리별 섹션**: 6개 카테고리로 분류
- **game_relevance 필터링**: 0.5 이상만 포함
- **반응형 디자인**: 모바일 최적화

### 웹훅 전송 데이터

```json
{
  "html": "<!DOCTYPE html>..."
}
```

## 설정

### GitHub Secrets

GitHub Actions에서 사용할 Secrets 설정:

1. GitHub 저장소 > Settings > Secrets and variables > Actions
2. `CLAUDE_API_KEY` 추가: Claude API 키

### main.py 설정

`main.py`에서 다음 설정을 변경할 수 있습니다:

- `WEBHOOK_URL`: Make.com 웹훅 URL
- `MAX_PAGE`: 크롤링할 페이지 수 (기본값: 2)
- `CLAUDE_MODEL`: Claude 모델명 (기본값: claude-sonnet-4-5-20250929)

## 수집 데이터

각 기사마다 다음 정보를 수집합니다:

- **원문 정보**:
  - 제목 (title)
  - URL (url)
  - 발행일 (date)
  - 댓글 수 (comments)
  - 썸네일 이미지 (thumbnail)
  - 본문 내용 (body)
  - 미디어 출처 (media)

- **AI 처리 정보**:
  - 한국어 제목 (title_kr)
  - 한국어 요약 (content_summary_kr)
  - 카테고리 (category)
  - 게임 연관도 (game_relevance)

## 카테고리

- **규제 & 이슈**: 게임 산업의 규제, 문제점, 논란, 법적 이슈
- **게임 출시 & 발표**: 새로운 게임 출시, 개발 발표, 출시일 공개
- **매출 & 성과**: 게임 판매 실적, 수익, 플레이어 수, 비즈니스 전략
- **업데이트 & 패치**: 게임 패치, 기능 업데이트, 버그 수정
- **IP & 콜라보**: 게임 IP 관련 뉴스, 협업, 미디어 확장
- **커뮤니티 & 이벤트**: 게임 이벤트, 팬 행사, 프로모션

## 라이선스

MIT License

