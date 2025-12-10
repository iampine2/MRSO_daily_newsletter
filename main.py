"""
게임 뉴스 크롤링 통합 코드 (KST 기준 24시간 이내 필터링)
IGN, GameSpot, Gamelook에서 최신 게임 뉴스를 자동으로 수집합니다.
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import pytz
import requests
import time
import re
from dateutil import parser as date_parser
from anthropic import Anthropic
import os

# 설정
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://hook.us2.make.com/x66njlvg1dx6jxethzuy4n92w4xrgua5')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
MAX_PAGE = 2
KST = pytz.timezone('Asia/Seoul')

# Claude 클라이언트 초기화
if not CLAUDE_API_KEY:
    raise ValueError("CLAUDE_API_KEY 환경변수가 설정되지 않았습니다!")
anthropic_client = Anthropic(api_key=CLAUDE_API_KEY)

def setup_driver():
    """Chrome 드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # 새로운 headless 모드
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--remote-debugging-port=9222')  # 디버깅 포트
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # 로그 레벨 설정
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    print('Chrome 드라이버 초기화 중...')
    driver = webdriver.Chrome(options=chrome_options)
    
    # 타임아웃 설정
    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)
    driver.implicitly_wait(10)
    
    print('Chrome 드라이버 초기화 완료!')
    return driver

def is_within_24_hours(article_time_kst, now_kst):
    """24시간 이내 기사인지 확인"""
    diff = now_kst - article_time_kst
    return diff.total_seconds() / 3600 <= 24

def generate_daily_summary(articles):
    """Claude API를 사용하여 오늘의 게임 산업 트렌드 분석 (4개 불릿)"""
    try:
        # 상위 30개 기사의 제목과 요약만 추출
        article_summaries = []
        for i, article in enumerate(articles[:30], 1):
            category = article.get('category', '기타')
            article_summaries.append(f"{i}. [{category}] {article.get('title_kr', article.get('title', ''))}\n   {article.get('content_summary_kr', '')[:100]}...")
        
        articles_text = "\n\n".join(article_summaries)
        
        prompt = f"""당신은 게임 산업 분석가입니다. 오늘 수집된 뉴스 기사들을 분석하여 **구체적인 사례 기반의 산업 트렌드**를 파악해주세요.

수집된 기사들:
{articles_text}

분석 요구사항:
1. **반드시 구체적인 게임명, 회사명, 사례를 언급**하면서 트렌드 설명
2. 여러 기사에서 공통적으로 나타나는 주제나 패턴을 **실제 사례와 함께** 제시
3. "~경향", "~추세" 같은 추상적 표현보다는 **"A사의 B게임 전략"** 같은 구체적 표현 사용
4. 단순 나열이 아닌, 사례를 통해 산업의 변화 방향을 보여줄 것

출력 형식:
- 정확히 4개의 불릿 포인트
- 각 불릿은 1-2문장 (최대 100자)
- 명사형 종결어미 사용
- **반드시 구체적인 게임명/회사명/수치 포함**

좋은 예시:
• Call of Duty 시리즈의 연속 출시 중단 결정으로 Activision의 장기 개발 전략 전환
• Battlefield 6의 Wicked Grin 스킨 논란으로 게임 내 과금 콘텐츠에 대한 커뮤니티 반발 심화
• Assassin's Creed Black Flag 리메이크 발표로 Ubisoft의 IP 재활용 전략 본격화
• Lenovo Legion 게임 노트북의 투명 디스플레이 탑재로 게임 하드웨어 차별화 경쟁 가속

나쁜 예시 (너무 추상적):
• AAA급 게임 개발 주기 장기화 추세
• 게임 유통 구조 재편 가속화

형식:
• [구체적 사례 기반 트렌드 1]
• [구체적 사례 기반 트렌드 2]
• [구체적 사례 기반 트렌드 3]
• [구체적 사례 기반 트렌드 4]"""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        summary = response.content[0].text.strip()
        return summary
        
    except Exception as e:
        print(f"[ERROR] AI Summary 생성 실패: {e}")
        return "• 오늘의 게임 산업 트렌드를 분석 중입니다.\n• 주요 이슈를 정리하고 있습니다.\n• 업데이트 소식을 확인 중입니다.\n• 산업 동향을 모니터링하고 있습니다."

def translate_and_summarize(title, content):
    """Claude API를 사용하여 제목 번역, 본문 요약, 카테고리 분류, 중요도 평가"""
    try:
        prompt = f"""다음 게임 뉴스 기사를 분석하고 한국어로 번역 및 요약해주세요.

제목: {title}

본문:
{content}

요구사항:
1. 제목은 한국어로 자연스럽게 번역
2. 본문은 핵심 내용을 두괄식으로 2-3문장으로 요약하되, **종결어미를 명사형으로 작성** (예: ~함, ~발표, ~공개, ~선언, ~종료 등)
3. 게임명, 회사명, 인물명은 원문 유지 (예: "Star Wars", "Nintendo", "John Smith")
4. 번역체가 아닌 자연스러운 한국어 사용
5. 카테고리 분류:
   - "규제 & 이슈": 게임 산업의 규제, 문제점, 논란, 법적 이슈, 기술/운영 문제
   - "게임 출시 & 발표": 새로운 게임 출시, 개발 발표, 출시일 공개
   - "매출 & 성과": 게임 판매 실적, 수익, 플레이어 수, 비즈니스 전략, 산업 성장/현황
   - "업데이트 & 패치": 게임 패치, 기능 업데이트, 버그 수정
   - "IP & 콜라보": 게임 IP 관련 뉴스, 협업, 미디어 확장(영화, 시리즈 등)
   - "커뮤니티 & 이벤트": 게임 이벤트, 팬 행사, 프로모션
6. 게임 연관도 (game_relevance): 0~1 사이의 값으로 평가
   - 1.0: 게임 개발, 출시, 업데이트 등 게임 자체에 대한 내용
   - 0.5~0.9: 게임 IP를 활용한 다른 미디어 (영화, 애니메이션 등)
   - 0~0.4: 게임과 거의 무관한 내용
7. 기사 중요도 (importance): 0~1 사이의 값으로 평가 (0.4 이상이 중요)
   
   **매우 낮음 (0.0~0.2):**
   - 특별 할인, 세일 정보
   - 무료 배포 소식
   - 게이밍 기어 (노트북, 헤드셋, 키보드, 마우스) 관련 정보
   
   **낮음 (0.2~0.4):**
   - 게임의 단순한 기능 추가, 마이너 패치노트
   - 게임 공략 및 가이드
   - 일반적인 게임 플레이 팁
   
   **높음 (0.4~0.7):**
   - 신작 게임 출시 정보
   - 게임 업데이트 및 메이저 패치
   - 게임 IP 관련 미디어 확장 (영화, 드라마 등)
   
   **매우 높음 (0.7~1.0):**
   - 산업 보고서, 시장 분석
   - 규제 및 법적 이슈
   - 게임사 전략 변화, 비즈니스 모델 전환
   - 유저 동향 및 커뮤니티 반응 분석
   - 게임 산업 전반에 영향을 미치는 뉴스

응답 형식 (JSON):
{{
  "title_kr": "번역된 제목",
  "content_summary_kr": "명사형 종결어미로 작성된 요약",
  "category": "카테고리명",
  "game_relevance": 0.0,
  "importance": 0.0
}}"""

        message = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # 응답 파싱
        response_text = message.content[0].text
        
        # JSON 파싱 시도
        import json
        # JSON 블록 추출 (```json ... ``` 형태일 수 있음)
        if '```json' in response_text:
            json_start = response_text.find('```json') + 7
            json_end = response_text.find('```', json_start)
            response_text = response_text[json_start:json_end].strip()
        elif '```' in response_text:
            json_start = response_text.find('```') + 3
            json_end = response_text.find('```', json_start)
            response_text = response_text[json_start:json_end].strip()
        
        result = json.loads(response_text)
        return (
            result.get('title_kr', title),
            result.get('content_summary_kr', content[:200]),
            result.get('category', '기타'),
            result.get('game_relevance', 1.0),
            result.get('importance', 0.5)
        )
        
    except Exception as e:
        print(f'   [WARN] 번역/요약 실패: {e}')
        return title, content[:200], '기타', 1.0, 0.5  # 실패시 기본값 반환

def crawl_gamespot(driver, now_kst):
    """GameSpot 크롤링"""
    print('>> [GameSpot] 크롤링 중...')
    articles = []
    
    for page_num in range(1, MAX_PAGE + 1):
        url = 'https://www.gamespot.com/news/' if page_num == 1 else f'https://www.gamespot.com/news/?page={page_num}'
        
        try:
            driver.get(url)
            time.sleep(2)
        except Exception as e:
            print(f'   GameSpot 페이지 {page_num} 로드 실패: {e}')
            continue
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.card-item'))
            )
        except:
            continue
        
        # 기사 목록 추출
        cards = driver.find_elements(By.CSS_SELECTOR, '.card-item')
        
        for card in cards:
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, 'h4.card-item__title')
                link_elem = card.find_element(By.CSS_SELECTOR, 'a.card-item__link')
                time_elem = card.find_element(By.CSS_SELECTOR, 'div.symbol-text')
                
                title = title_elem.text.strip()
                url = link_elem.get_attribute('href')
                date_text = time_elem.get_attribute('title').replace('Updated on: ', '').strip()
                
                # 댓글 수
                try:
                    comment_spans = card.find_elements(By.CSS_SELECTOR, 'span.text-small')
                    comments = int(re.sub(r'\D', '', comment_spans[1].text)) if len(comment_spans) > 1 else 0
                except:
                    comments = 0
                
                # 날짜 파싱 (PST -> KST)
                try:
                    pst = pytz.timezone('America/Los_Angeles')
                    # "Dec" 같은 축약형 월 이름 처리
                    article_time_pst = datetime.strptime(date_text, '%A, %b %d, %Y %I:%M%p')
                    article_time_pst = pst.localize(article_time_pst)
                    article_time_kst = article_time_pst.astimezone(KST)
                    
                    if not is_within_24_hours(article_time_kst, now_kst):
                        continue
                    
                    # 본문 크롤링
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[-1])
                    
                    body_text = ''
                    thumbnail = ''
                    try:
                        driver.get(url)
                        time.sleep(1)
                        
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.article-body'))
                        )
                        paragraphs = driver.find_elements(By.CSS_SELECTOR, '.article-body p')
                        body_text = '\n'.join([p.text.strip() for p in paragraphs if p.text.strip()])
                        
                        # 썸네일
                        og_image = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
                        thumbnail = og_image.get_attribute('content')
                    except Exception as e:
                        print(f'   GameSpot 상세 페이지 로드 실패: {url[:50]}...')
                    
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    
                    articles.append({
                        'title': title,
                        'url': url,
                        'date': article_time_kst.strftime('%Y-%m-%d %H:%M'),
                        'comments': comments,
                        'thumbnail': thumbnail,
                        'body': body_text[:1000],
                        'media': 'GameSpot'
                    })
                    
                except Exception as e:
                    continue
                    
            except Exception as e:
                continue
    
    return articles

def crawl_gamelook(driver, now_kst):
    """Gamelook 크롤링"""
    print('>> [Gamelook] 크롤링 중...')
    articles = []
    
    for page_num in range(1, MAX_PAGE + 1):
        url = 'http://www.gamelook.com.cn/' if page_num == 1 else f'http://www.gamelook.com.cn/page/{page_num}/'
        
        try:
            driver.get(url)
            time.sleep(2)
        except Exception as e:
            print(f'   Gamelook 페이지 {page_num} 로드 실패: {e}')
            continue
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li.item'))
            )
        except:
            continue
        
        # 기사 목록 추출
        items = driver.find_elements(By.CSS_SELECTOR, 'li.item')
        
        for item in items:
            try:
                # 제목과 링크
                title_elem = item.find_element(By.CSS_SELECTOR, 'h2.item-title a')
                title = title_elem.text.strip()
                url = title_elem.get_attribute('href')
                
                # 썸네일
                thumbnail = ''
                try:
                    img_elem = item.find_element(By.CSS_SELECTOR, '.item-img img')
                    thumbnail = img_elem.get_attribute('data-original') or img_elem.get_attribute('src')
                except:
                    pass
                
                # 날짜
                try:
                    date_elem = item.find_element(By.CSS_SELECTOR, '.item-meta .date')
                    date_text = date_elem.text.strip()  # "2025-12-05"
                    
                    # KST로 파싱 (중국 시간 = UTC+8, KST = UTC+9, 1시간 차이)
                    china_tz = pytz.timezone('Asia/Shanghai')
                    article_time_china = datetime.strptime(date_text, '%Y-%m-%d')
                    article_time_china = china_tz.localize(article_time_china)
                    article_time_kst = article_time_china.astimezone(KST)
                    
                    if not is_within_24_hours(article_time_kst, now_kst):
                        continue
                    
                except:
                    continue
                
                # 본문 크롤링
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                
                body_text = ''
                try:
                    driver.get(url)
                    time.sleep(1)
                    
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))
                    )
                    paragraphs = driver.find_elements(By.CSS_SELECTOR, 'article p')
                    body_text = '\n'.join([p.text.strip() for p in paragraphs if p.text.strip()])
                except Exception as e:
                    print(f'   Gamelook 상세 페이지 로드 실패: {url[:50]}...')
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                
                articles.append({
                    'title': title,
                    'url': url,
                    'date': article_time_kst.strftime('%Y-%m-%d %H:%M'),
                    'comments': 0,  # Gamelook은 댓글 수 없음
                    'thumbnail': thumbnail,
                    'body': body_text[:1000],
                    'media': 'Gamelook'
                })
                
            except Exception as e:
                try:
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                except:
                    pass
                continue
    
    return articles

def crawl_ign(driver, now_kst):
    """IGN 크롤링"""
    print('>> [IGN] 크롤링 중...')
    articles = []
    
    try:
        print('   IGN 메인 페이지 로딩...')
        driver.get('https://www.ign.com/news')
        time.sleep(3)
        print('   IGN 메인 페이지 로드 완료')
    except Exception as e:
        print(f'   IGN 페이지 로드 실패: {e}')
        return articles
    
    # 스크롤해서 더 많은 기사 로드 (24시간 내 모든 기사 로드)
    try:
        print('   IGN 페이지 스크롤 중... (더 많은 기사 로드)')
        for i in range(5):  # 3 → 5로 증가
            driver.execute_script('window.scrollBy(0, document.body.scrollHeight)')
            time.sleep(1.5)
            print(f'   스크롤 {i+1}/5 완료')
    except Exception as e:
        print(f'   스크롤 실패: {e}')
    
    try:
        print('   IGN 기사 카드 대기 중...')
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-cy="item-details"]'))
        )
        print('   IGN 기사 카드 발견!')
    except Exception as e:
        print(f'   IGN 기사 카드를 찾을 수 없음: {e}')
        return articles
    
    cards = driver.find_elements(By.CSS_SELECTOR, '[data-cy="item-details"]')
    print(f'   IGN 총 {len(cards)}개 카드 발견')
    
    # 최대 10개 처리 (타임아웃 방지) + 24시간 내 기사만 수집
    processed_count = 0
    max_articles = 10
    
    for idx, card in enumerate(cards, 1):
        if processed_count >= max_articles:
            print(f'   최대 {max_articles}개 처리 완료 - 중단')
            break
            
        try:
            print(f'   IGN 기사 {idx}/{min(len(cards), max_articles)} 처리 중...')
            title_elem = card.find_element(By.CSS_SELECTOR, '[data-cy="item-title"]')
            title = title_elem.text.strip()
            
            # 링크
            parent_link = card.find_element(By.XPATH, './ancestor::a[@class="item-body"]')
            url = parent_link.get_attribute('href')
            if url.startswith('/'):
                url = 'https://www.ign.com' + url
            
            print(f'   제목: {title[:50]}...')
            
            # 댓글 수
            try:
                comment_elem = card.find_element(By.CSS_SELECTOR, '.comment-count')
                comments = int(re.sub(r'\D', '', comment_elem.text))
            except:
                comments = 0
            
            # 상세 페이지에서 날짜 확인
            print(f'   상세 페이지 열기: {url[:50]}...')
            sys.stdout.flush()
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            
            # 상세 페이지 로드 타임아웃을 10초로 제한
            driver.set_page_load_timeout(10)
            
            try:
                driver.get(url)
                time.sleep(1)
                print(f'   상세 페이지 로드 완료')
                sys.stdout.flush()
            except Exception as e:
                print(f'   IGN 상세 페이지 로드 실패 (10초 타임아웃): {str(e)[:50]}')
                sys.stdout.flush()
                driver.set_page_load_timeout(30)  # 원래대로 복구
                try:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                except:
                    pass
                continue
            finally:
                driver.set_page_load_timeout(30)  # 원래대로 복구
            
            try:
                print(f'   메타데이터 파싱 중...')
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'main'))
                )
                
                # 날짜 파싱
                published_meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="article:published_time"]')
                published_time = published_meta.get_attribute('content')
                
                article_time_kst = date_parser.parse(published_time).astimezone(KST)
                print(f'   날짜: {article_time_kst.strftime("%Y-%m-%d %H:%M")}')
                
                if not is_within_24_hours(article_time_kst, now_kst):
                    print(f'   24시간 이내 기사 아님 - 스킵')
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue
                
                # 본문
                paragraphs = driver.find_elements(By.CSS_SELECTOR, 'main p')
                body_text = '\n'.join([p.text.strip() for p in paragraphs if p.text.strip()])
                print(f'   본문 길이: {len(body_text)}자')
                
                # 썸네일
                thumbnail = ''
                try:
                    og_image = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
                    thumbnail = og_image.get_attribute('content')
                except:
                    pass
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                
                articles.append({
                    'title': title,
                    'url': url,
                    'date': article_time_kst.strftime('%Y-%m-%d %H:%M'),
                    'comments': comments,
                    'thumbnail': thumbnail,
                    'body': body_text[:1000],
                    'media': 'IGN'
                })
                processed_count += 1  # 수집 성공 시 카운트 증가
                print(f'   ✅ IGN 기사 {idx} 수집 완료! (총 {processed_count}개)')
                
            except Exception as e:
                print(f'   ❌ IGN 기사 {idx} 처리 실패: {e}')
                try:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                except:
                    pass
                continue
                
        except Exception as e:
            continue
    
    return articles

def main():
    """메인 실행 함수"""
    import json
    import sys
    
    print('='*60)
    print('>> 게임 뉴스 크롤링 시작')
    print('='*60)
    sys.stdout.flush()  # 즉시 출력
    
    now_kst = datetime.now(KST)
    print(f'현재 시각 (KST): {now_kst.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'필터링 기준: 24시간 이내 기사\n')
    sys.stdout.flush()
    
    driver = setup_driver()
    all_articles = []
    
    try:
        # GameSpot 크롤링
        try:
            print('>> [GameSpot] 크롤링 시작...')
            sys.stdout.flush()
            gamespot_articles = crawl_gamespot(driver, now_kst)
            all_articles.extend(gamespot_articles)
            print(f'   GameSpot: {len(gamespot_articles)}개 수집')
            sys.stdout.flush()
        except Exception as e:
            print(f'   ❌ GameSpot 크롤링 실패: {e}')
            sys.stdout.flush()
        
        # IGN 크롤링 (재시도 로직 추가)
        ign_success = False
        max_retries = 3
        
        for retry in range(max_retries):
            try:
                if retry > 0:
                    print(f'>> [IGN] 재시도 {retry}/{max_retries-1}...')
                    sys.stdout.flush()
                    time.sleep(5)  # 재시도 전 대기
                else:
                    print('>> [IGN] 크롤링 시작...')
                    sys.stdout.flush()
                
                ign_articles = crawl_ign(driver, now_kst)
                all_articles.extend(ign_articles)
                print(f'   IGN: {len(ign_articles)}개 수집')
                sys.stdout.flush()
                ign_success = True
                break
            except Exception as e:
                print(f'   ❌ IGN 크롤링 실패 (시도 {retry+1}/{max_retries}): {str(e)[:100]}')
                sys.stdout.flush()
                if retry == max_retries - 1:
                    print(f'   ⚠️ IGN 크롤링 최종 실패 - GameSpot과 Gamelook으로 계속 진행')
                    sys.stdout.flush()
        
        # Gamelook 크롤링
        try:
            print('>> [Gamelook] 크롤링 시작...')
            sys.stdout.flush()
            gamelook_articles = crawl_gamelook(driver, now_kst)
            all_articles.extend(gamelook_articles)
            print(f'   Gamelook: {len(gamelook_articles)}개 수집')
            sys.stdout.flush()
        except Exception as e:
            print(f'   ❌ Gamelook 크롤링 실패: {e}')
            sys.stdout.flush()
        
    finally:
        print('Chrome 드라이버 종료 중...')
        sys.stdout.flush()
        driver.quit()
        print('Chrome 드라이버 종료 완료!')
        sys.stdout.flush()
    
    print(f'\n>> 수집 완료! 총 {len(all_articles)}개 기사')
    sys.stdout.flush()
    
    # 댓글 수 기준 정렬
    print('>> 댓글 수 기준 정렬 중...')
    sys.stdout.flush()
    all_articles.sort(key=lambda x: x.get('comments', 0), reverse=True)
    print('>> 정렬 완료!')
    sys.stdout.flush()
    
    print(f'\n총 수집 기사: {len(all_articles)}개')
    sys.stdout.flush()
    
    if all_articles:
        # 번역 및 요약 처리
        print(f'\n>> 번역, 요약 및 카테고리 분류 중...')
        sys.stdout.flush()
        for i, article in enumerate(all_articles, 1):
            print(f'   [{i}/{len(all_articles)}] {article["media"]} - {article["title"][:50]}...')
            sys.stdout.flush()
            
            try:
                title_kr, content_summary_kr, category, game_relevance, importance = translate_and_summarize(
                    article['title'], 
                    article['body']
                )
                article['title_kr'] = title_kr
                article['content_summary_kr'] = content_summary_kr
                article['category'] = category
                article['game_relevance'] = game_relevance
                article['importance'] = importance
                print(f'   ✅ 번역 완료: {title_kr[:30]}... (중요도: {importance:.2f})')
                sys.stdout.flush()
            except Exception as e:
                print(f'   ❌ 번역 실패: {e}')
                article['title_kr'] = article['title']
                article['content_summary_kr'] = article['body'][:200]
                article['category'] = '기타'
                article['game_relevance'] = 1.0
                article['importance'] = 0.5
                sys.stdout.flush()
            
            time.sleep(0.5)  # API 호출 간격
        
        # AI Summary 생성
        print(f'\n>> AI Summary 생성 중...')
        sys.stdout.flush()
        daily_summary = generate_daily_summary(all_articles)
        print(f'✅ AI Summary 생성 완료')
        sys.stdout.flush()
        
        # JSON 파일로 저장
        output_file = 'collected_articles.json'
        
        # JSON 파일 저장 (AI Summary 포함)
        output_data = {
            'daily_summary': daily_summary,
            'articles': all_articles
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        total_body_length = sum(len(article['body']) for article in all_articles)
        
        print(f'\n결과 저장: {output_file}')
        print(f'본문 총 글자 수: {total_body_length}')
        
        # HTML 뉴스레터 생성
        print(f'\n>> HTML 뉴스레터 생성 중...')
        import subprocess
        subprocess.run(['python', 'generate_html.py'], check=True)
        
        # HTML 파일 읽기
        with open('daily_newsletter.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 웹훅 전송 (HTML 형태로)
        print(f'\n>> 웹훅 전송 중...')
        try:
            response = requests.post(
                WEBHOOK_URL,
                json={'html': html_content},
                timeout=30
            )
            if response.status_code == 200:
                print(f'✅ 웹훅 전송 성공! (응답: {response.status_code})')
            else:
                print(f'❌ 웹훅 응답: {response.status_code}')
        except Exception as e:
            print(f'❌ 웹훅 전송 실패: {e}')
    else:
        print('조건에 맞는 기사가 없습니다.')
    
    print('\n' + '='*60)

if __name__ == '__main__':
    main()

