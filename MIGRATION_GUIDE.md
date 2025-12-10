# 🚀 Public GitHub 마이그레이션 가이드

## ✅ 완료된 작업
- [x] Workflow 파일 수정 (ubuntu-latest로 변경)
- [x] Chrome/ChromeDriver 자동 설치 추가

## 📋 진행 단계

### 1️⃣ 새 Public Repository 생성

1. https://github.com/iampine2 로그인
2. 우측 상단 **+** 클릭 → **New repository**
3. 설정:
   - Repository name: `MRSO_daily_newsletter`
   - Description: "Daily Game Industry Newsletter Crawler"
   - **Public** 선택 ⭐ (중요!)
   - ❌ README, .gitignore, license 추가 안 함 (이미 있음)
4. **Create repository** 클릭

### 2️⃣ Remote 변경 및 푸시

PowerShell에서 실행:

```powershell
cd C:\Users\iampine\MRSO_daily_newsletter

# 기존 remote 확인
git remote -v

# 기존 remote 제거
git remote remove origin

# 새 remote 추가
git remote add origin https://github.com/iampine2/MRSO_daily_newsletter.git

# 푸시
git push -u origin main
```

만약 인증 오류가 나면:
```powershell
# Personal Access Token 사용
git push -u origin main
# Username: iampine2
# Password: [GitHub Personal Access Token]
```

### 3️⃣ GitHub Secrets 설정

https://github.com/iampine2/MRSO_daily_newsletter/settings/secrets/actions

**New repository secret** 클릭하여 2개 추가:

#### Secret 1: CLAUDE_API_KEY
- Name: `CLAUDE_API_KEY`
- Secret: `[Claude API 키]`

#### Secret 2: WEBHOOK_URL
- Name: `WEBHOOK_URL`
- Secret: `https://hook.us2.make.com/x66njlvg1dx6jxethzuy4n92w4xrgua5`

### 4️⃣ 테스트 실행

1. https://github.com/iampine2/MRSO_daily_newsletter/actions
2. 좌측 **Daily News Crawler** 클릭
3. 우측 **Run workflow** → **Run workflow** 클릭
4. 실행 확인! 🎉

### 5️⃣ Self-hosted Runner 정리 (선택사항)

더 이상 필요 없으므로:

```powershell
# Runner 중지 (Ctrl+C로 종료)
# 또는 서비스로 설치했다면:
cd C:\actions-runner
.\svc.sh uninstall  # 서비스 제거
```

## 🎯 완료 후 확인사항

✅ PC 꺼져도 매일 오전 9시(KST) 자동 실행
✅ 결과는 GitHub에 자동 커밋
✅ Make.com 웹훅으로 HTML 전송
✅ 무료, 무제한 실행!

## ⚠️ 보안 체크리스트

- [x] API 키는 Secrets에 저장 (코드에 없음)
- [x] 웹훅 URL도 Secrets에 저장
- [x] .gitignore에 민감 정보 제외
- [x] Public repo이지만 안전함!

## 🆘 문제 발생 시

### Personal Access Token 생성 (인증 필요 시)
1. https://github.com/settings/tokens
2. **Generate new token** → **Classic**
3. Note: "MRSO Newsletter"
4. Expiration: 90 days (또는 원하는 기간)
5. Scopes: `repo` 전체 체크
6. **Generate token**
7. 토큰 복사 (다시 볼 수 없음!)

### Workflow 실행 실패 시
- Actions 탭에서 로그 확인
- Chrome 설치 문제일 경우 workflow 파일 수정 필요

