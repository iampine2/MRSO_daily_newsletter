# Public GitHub으로 마이그레이션 가이드

## 1️⃣ 새 Public Repository 생성

1. https://github.com 로그인
2. New repository 클릭
3. Repository name: `MRSO_daily_newsletter`
4. **Public** 선택 (무료 GitHub Actions 사용)
5. Create repository

## 2️⃣ 코드 푸시

```bash
cd C:\Users\iampine\MRSO_daily_newsletter

# 기존 remote 제거
git remote remove origin

# 새 remote 추가 (본인의 GitHub 계정)
git remote add origin https://github.com/[your-username]/MRSO_daily_newsletter.git

# 푸시
git push -u origin main
```

## 3️⃣ Secrets 설정

GitHub 저장소 Settings → Secrets and variables → Actions:
- `CLAUDE_API_KEY`: Claude API 키
- `WEBHOOK_URL`: Make.com 웹훅 URL

## 4️⃣ Workflow 파일 수정

`.github/workflows/daily-crawler.yml`을 다시 `ubuntu-latest`로 변경:

```yaml
jobs:
  crawl:
    runs-on: ubuntu-latest  # Self-hosted 대신 ubuntu-latest
```

## 5️⃣ 완료!

이제 PC 꺼져도 매일 자동으로 실행됩니다! 🎉

## ⚠️ 주의사항

### Public Repository 보안:
- ✅ API 키는 Secrets에 저장 (안전)
- ✅ 코드는 공개됨 (문제 없음)
- ⚠️ 민감한 정보는 절대 코드에 직접 넣지 말 것

### Private Repository로 하려면:
- GitHub Pro 필요 ($4/월)
- 또는 무료 플랜 (월 2,000분 제한)


