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
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    # 페이지 로드 타임아웃 설정 (30초)
    driver.set_page_load_timeout(30)
    return driver

def is_within_24_hours(article_time_kst, now_kst):
    """24시간 이내 기사인지 확인"""
    diff = now_kst - article_time_kst
    return diff.total_seconds() / 3600 <= 24

def generate_daily_summary(articles):
    """Claude API를 사용하여 오늘의 게임 산업 트렌드 요약 (4개 불릿)"""
    try:
        # 상위 20개 기사의 제목과 요약만 추출
        article_summaries = []
        for i, article in enumerate(articles[:20], 1):
            article_summaries.append(f"{i}. [{article.get('media', 'Unknown')}] {article.get('title_kr', article.get('title', ''))}\n   요약: {article.get('content_summary_kr', '')[:100]}...")
        
        articles_text = "\n\n".join(article_summaries)
        
        prompt = f"""다음은 오늘 수집된 게임 산업 뉴스 기사들입니다. 이 기사들을 분석하여 오늘의 주요 게임 산업 트렌드와 이슈를 **4개의 불릿 포인트**로 요약해주세요.

수집된 기사들:
{articles_text}

요구사항:
1. 정확히 4개의 불릿 포인트로 작성
2. 각 불릿은 한 문장으로 간결하게 (최대 50자)
3. 가장 중요하고 영향력 있는 트렌드 위주로 선정
4. 구체적인 게임명, 회사명 포함
5. 명사형 종결어미 사용 (예: ~발표, ~출시, ~논란, ~성장)

형식:
• [불릿 1]
• [불릿 2]
• [불릿 3]
• [불릿 4]"""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        summary = response.content[0].text.strip()
        return summary
        
    except Exception as e:
        print(f"[ERROR] AI Summary 생성 실패: {e}")
        return "• 오늘의 게임 산업 트렌드를 분석 중입니다.\n• 주요 이슈를 정리하고 있습니다.\n• 업데이트 소식을 확인 중입니다.\n• 산업 동향을 모니터링하고 있습니다."

def translate_and_summarize(title, content):
    """Claude API를 사용하여 제목 번역, 본문 요약, 카테고리 분류"""
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

응답 형식 (JSON):
{{
  "title_kr": "번역된 제목",
  "content_summary_kr": "명사형 종결어미로 작성된 요약",
  "category": "카테고리명",
  "game_relevance": 0.0
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
            result.get('game_relevance', 1.0)
        )
        
    except Exception as e:
        print(f'   [WARN] 번역/요약 실패: {e}')
        return title, content[:200], '기타', 1.0  # 실패시 기본값 반환

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
        driver.get('https://www.ign.com/news')
        time.sleep(2)
    except Exception as e:
        print(f'   IGN 페이지 로드 실패: {e}')
        return articles
    
    # 스크롤해서 더 많은 기사 로드
    for _ in range(3):
        driver.execute_script('window.scrollBy(0, document.body.scrollHeight)')
        time.sleep(1.5)
    
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-cy="item-details"]'))
        )
    except:
        return articles
    
    cards = driver.find_elements(By.CSS_SELECTOR, '[data-cy="item-details"]')
    
    for card in cards:
        try:
            title_elem = card.find_element(By.CSS_SELECTOR, '[data-cy="item-title"]')
            title = title_elem.text.strip()
            
            # 링크
            parent_link = card.find_element(By.XPATH, './ancestor::a[@class="item-body"]')
            url = parent_link.get_attribute('href')
            if url.startswith('/'):
                url = 'https://www.ign.com' + url
            
            # 댓글 수
            try:
                comment_elem = card.find_element(By.CSS_SELECTOR, '.comment-count')
                comments = int(re.sub(r'\D', '', comment_elem.text))
            except:
                comments = 0
            
            # 상세 페이지에서 날짜 확인
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            
            try:
                driver.get(url)
                time.sleep(1)
            except Exception as e:
                print(f'   IGN 상세 페이지 로드 실패: {url[:50]}...')
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                continue
            
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'main'))
                )
                
                # 날짜 파싱
                published_meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="article:published_time"]')
                published_time = published_meta.get_attribute('content')
                
                article_time_kst = date_parser.parse(published_time).astimezone(KST)
                
                if not is_within_24_hours(article_time_kst, now_kst):
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue
                
                # 본문
                paragraphs = driver.find_elements(By.CSS_SELECTOR, 'main p')
                body_text = '\n'.join([p.text.strip() for p in paragraphs if p.text.strip()])
                
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
                
            except Exception as e:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                continue
                
        except Exception as e:
            continue
    
    return articles

def main():
    """메인 실행 함수"""
    import json
    
    print('='*60)
    print('>> 게임 뉴스 크롤링 시작')
    print('='*60)
    
    now_kst = datetime.now(KST)
    print(f'현재 시각 (KST): {now_kst.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'필터링 기준: 24시간 이내 기사\n')
    
    driver = setup_driver()
    all_articles = []
    
    try:
        # GameSpot 크롤링
        try:
            gamespot_articles = crawl_gamespot(driver, now_kst)
            all_articles.extend(gamespot_articles)
            print(f'   GameSpot: {len(gamespot_articles)}개 수집')
        except Exception as e:
            print(f'   ❌ GameSpot 크롤링 실패: {e}')
        
        # IGN 크롤링
        try:
            ign_articles = crawl_ign(driver, now_kst)
            all_articles.extend(ign_articles)
            print(f'   IGN: {len(ign_articles)}개 수집')
        except Exception as e:
            print(f'   ❌ IGN 크롤링 실패: {e}')
        
        # Gamelook 크롤링
        try:
            gamelook_articles = crawl_gamelook(driver, now_kst)
            all_articles.extend(gamelook_articles)
            print(f'   Gamelook: {len(gamelook_articles)}개 수집')
        except Exception as e:
            print(f'   ❌ Gamelook 크롤링 실패: {e}')
        
    finally:
        driver.quit()
    
    # 댓글 수 기준 정렬
    all_articles.sort(key=lambda x: x['comments'], reverse=True)
    
    print(f'\n총 수집 기사: {len(all_articles)}개')
    
    if all_articles:
        # 번역 및 요약 처리
        print(f'\n>> 번역, 요약 및 카테고리 분류 중...')
        for i, article in enumerate(all_articles, 1):
            print(f'   [{i}/{len(all_articles)}] {article["media"]} - {article["title"][:50]}...')
            title_kr, content_summary_kr, category, game_relevance = translate_and_summarize(
                article['title'], 
                article['body']
            )
            article['title_kr'] = title_kr
            article['content_summary_kr'] = content_summary_kr
            article['category'] = category
            article['game_relevance'] = game_relevance
            time.sleep(0.5)  # API 호출 간격
        
        # AI Summary 생성
        print(f'\n>> AI Summary 생성 중...')
        daily_summary = generate_daily_summary(all_articles)
        print(f'✅ AI Summary 생성 완료')
        
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

