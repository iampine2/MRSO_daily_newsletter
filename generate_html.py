"""JSON 데이터를 HTML 뉴스레터로 변환"""
import json
from datetime import datetime
import pytz

def load_articles():
    """collected_articles.json 로드"""
    try:
        with open('collected_articles.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 새로운 형식 (daily_summary + articles) 또는 기존 형식 (배열) 처리
            if isinstance(data, dict) and 'articles' in data:
                return data
            else:
                # 기존 형식 (배열)
                return {'daily_summary': '', 'articles': data}
    except FileNotFoundError:
        print("[ERROR] collected_articles.json 파일을 찾을 수 없습니다.")
        return {'daily_summary': '', 'articles': []}

def filter_articles(articles):
    """game_relevance 0.5 이상 AND importance 0.4 이상만 필터링"""
    return [a for a in articles 
            if a.get('game_relevance', 0) >= 0.5 
            and a.get('importance', 0) >= 0.4]

def get_hot_trend_articles(articles):
    """댓글 10개 이상인 기사를 댓글 수 내림차순으로 정렬"""
    hot = [a for a in articles if a.get('comments', 0) >= 10]
    return sorted(hot, key=lambda x: x.get('comments', 0), reverse=True)

def categorize_articles(articles):
    """카테고리별로 기사 분류"""
    categories = {
        '규제 & 이슈': [],
        '게임 출시 & 발표': [],
        '매출 & 성과': [],
        '업데이트 & 패치': [],
        'IP & 콜라보': [],
        '커뮤니티 & 이벤트': []
    }
    
    for article in articles:
        cat = article.get('category', '기타')
        if cat in categories:
            categories[cat].append(article)
    
    return categories

def escape_html(text):
    """HTML 특수문자 이스케이프"""
    if not text:
        return ""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

def format_date(date_str):
    """날짜 포맷팅 (YYYY-MM-DD HH:MM -> MM.DD)"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        return dt.strftime('%m.%d')
    except:
        return date_str

def truncate_summary(text, max_length=200):
    """요약문을 최대 길이로 제한"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def generate_hot_section(hot_articles):
    """HOT TREND 섹션 생성 (최대 5개)"""
    if not hot_articles:
        return ""
    
    html = []
    
    # 1, 2번째 기사 (2 Column with image) - 높이 동일하게 (display: flex 사용)
    if len(hot_articles) >= 2:
        a1 = hot_articles[0]
        a2 = hot_articles[1]
        summary1 = a1.get('content_summary_kr', '')
        summary2 = a2.get('content_summary_kr', '')
        
        html.append(f"""
                    <!-- 2 Column HOT Items -->
                    <tr>
                        <td class="mobile-padding" style="padding: 20px 50px;">
                            <!--[if mso]>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td width="48%" valign="top" style="padding-right: 2%;">
                                        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8f8f8; border: 1px solid #e0e0e0;">
                                            <tr>
                                                <td style="padding: 0;">
                                                    <a href="{escape_html(a1.get('url', '#'))}" style="text-decoration: none;">
                                                        <img src="{escape_html(a1.get('thumbnail', ''))}" width="100%" height="200" style="display: block;" alt="{escape_html(a1.get('media', ''))}">
                                                    </a>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 25px;">
                                                    <a href="{escape_html(a1.get('url', '#'))}" style="text-decoration: none; color: #000000;">
                                                        <div style="padding-bottom: 10px;">
                                                            <font face="Malgun Gothic, Arial, sans-serif" style="font-size: 14px; font-weight: 700; color: #000000; line-height: 1.4;">{escape_html(a1.get('title_kr', a1.get('title', '')))}</font>
                                                        </div>
                                                        <div style="padding-bottom: 12px;">
                                                            <font face="Malgun Gothic, Arial, sans-serif" style="font-size: 13px; font-weight: 400; color: #666666; line-height: 1.5;">{escape_html(summary1)}</font>
                                                        </div>
                                                        <div>
                                                            <font face="Malgun Gothic, Arial, sans-serif" style="font-size: 11px; font-weight: 500; color: #999999;">{escape_html(a1.get('media', ''))} · {format_date(a1.get('date', ''))} · 💬 {a1.get('comments', 0)}</font>
                                                        </div>
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                    <td width="48%" valign="top" style="padding-left: 2%;">
                                        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8f8f8; border: 1px solid #e0e0e0;">
                                            <tr>
                                                <td style="padding: 0;">
                                                    <a href="{escape_html(a2.get('url', '#'))}" style="text-decoration: none;">
                                                        <img src="{escape_html(a2.get('thumbnail', ''))}" width="100%" height="200" style="display: block;" alt="{escape_html(a2.get('media', ''))}">
                                                    </a>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 25px;">
                                                    <a href="{escape_html(a2.get('url', '#'))}" style="text-decoration: none; color: #000000;">
                                                        <div style="padding-bottom: 10px;">
                                                            <font face="Malgun Gothic, Arial, sans-serif" style="font-size: 14px; font-weight: 700; color: #000000; line-height: 1.4;">{escape_html(a2.get('title_kr', a2.get('title', '')))}</font>
                                                        </div>
                                                        <div style="padding-bottom: 12px;">
                                                            <font face="Malgun Gothic, Arial, sans-serif" style="font-size: 13px; font-weight: 400; color: #666666; line-height: 1.5;">{escape_html(summary2)}</font>
                                                        </div>
                                                        <div>
                                                            <font face="Malgun Gothic, Arial, sans-serif" style="font-size: 11px; font-weight: 500; color: #999999;">{escape_html(a2.get('media', ''))} · {format_date(a2.get('date', ''))} · 💬 {a2.get('comments', 0)}</font>
                                                        </div>
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            <![endif]-->
                            <!--[if !mso]><!-->
                            <div style="display: flex; gap: 20px; width: 100%;">
                                <div class="two-col-left" style="flex: 1; min-width: 0;">
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8f8f8; border: 1px solid #e0e0e0; height: 100%;">
                                        <tr>
                                            <td style="padding: 0;">
                                                <a href="{escape_html(a1.get('url', '#'))}" style="text-decoration: none; display: block;">
                                                    <img src="{escape_html(a1.get('thumbnail', ''))}" width="100%" style="display: block; width: 100%; height: 200px; object-fit: cover;" alt="{escape_html(a1.get('media', ''))}">
                                                </a>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 25px;">
                                                <a href="{escape_html(a1.get('url', '#'))}" style="text-decoration: none; color: inherit; display: block;">
                                                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                                        <tr>
                                                            <td style="padding-bottom: 10px;">
                                                                <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 14px; font-weight: 700; color: #000000; line-height: 1.4;">{escape_html(a1.get('title_kr', a1.get('title', '')))}</font>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding-bottom: 12px;">
                                                                <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 13px; font-weight: 400; color: #666666; line-height: 1.5;">{escape_html(summary1)}</font>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td>
                                                                <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 11px; font-weight: 500; color: #999999;">{escape_html(a1.get('media', ''))} · {format_date(a1.get('date', ''))} · 💬 {a1.get('comments', 0)}</font>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                </div>
                                <div class="two-col-right" style="flex: 1; min-width: 0;">
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8f8f8; border: 1px solid #e0e0e0; height: 100%;">
                                        <tr>
                                            <td style="padding: 0;">
                                                <a href="{escape_html(a2.get('url', '#'))}" style="text-decoration: none; display: block;">
                                                    <img src="{escape_html(a2.get('thumbnail', ''))}" width="100%" style="display: block; width: 100%; height: 200px; object-fit: cover;" alt="{escape_html(a2.get('media', ''))}">
                                                </a>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 25px;">
                                                <a href="{escape_html(a2.get('url', '#'))}" style="text-decoration: none; color: inherit; display: block;">
                                                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                                        <tr>
                                                            <td style="padding-bottom: 10px;">
                                                                <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 14px; font-weight: 700; color: #000000; line-height: 1.4;">{escape_html(a2.get('title_kr', a2.get('title', '')))}</font>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding-bottom: 12px;">
                                                                <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 13px; font-weight: 400; color: #666666; line-height: 1.5;">{escape_html(summary2)}</font>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td>
                                                                <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 11px; font-weight: 500; color: #999999;">{escape_html(a2.get('media', ''))} · {format_date(a2.get('date', ''))} · 💬 {a2.get('comments', 0)}</font>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                            <!--<![endif]-->
                        </td>
                    </tr>
""")
    
    # 3, 4, 5번째 기사 (썸네일 + 텍스트) - 회색 배경 박스
    for rank in range(2, min(5, len(hot_articles))):
        a = hot_articles[rank]
        summary = a.get('content_summary_kr', '')  # 전체 요약 노출
        padding_bottom = "20px" if rank < 4 else "40px"
        
        html.append(f"""
                    <!-- HOT TREND #{rank + 1} (Thumbnail + Text with Gray Background) -->
                    <tr>
                        <td class="mobile-padding" style="padding: 0 50px {padding_bottom} 50px;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8f8f8; border: 1px solid #e0e0e0;">
                                <tr>
                                    <td width="250" style="padding: 0; vertical-align: top;">
                                        <a href="{escape_html(a.get('url', '#'))}" style="text-decoration: none; display: block;">
                                            <img src="{escape_html(a.get('thumbnail', ''))}" width="250" style="display: block; width: 250px; height: 100%; object-fit: cover; min-height: 200px;" alt="{escape_html(a.get('media', ''))}">
                                        </a>
                                    </td>
                                    <td style="padding: 25px; vertical-align: top;">
                                        <a href="{escape_html(a.get('url', '#'))}" style="text-decoration: none; color: inherit; display: block;">
                                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                                <tr>
                                                    <td style="padding-bottom: 8px;">
                                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 14px; font-weight: 700; color: #000000; line-height: 1.4;">{escape_html(a.get('title_kr', a.get('title', '')))}</font>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding-bottom: 10px;">
                                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 13px; font-weight: 400; color: #666666; line-height: 1.5;">{escape_html(summary)}</font>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td>
                                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 11px; font-weight: 500; color: #999999;">{escape_html(a.get('media', ''))} · {format_date(a.get('date', ''))} · 💬 {a.get('comments', 0)}</font>
                                                    </td>
                                                </tr>
                                            </table>
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
""")
    
    return ''.join(html)

def generate_category_section(category_name, articles, english_name):
    """카테고리 섹션 생성 (모든 기사 표시) - 작은 썸네일 + 첫 문장만"""
    if not articles:
        return ""
    
    icon = get_category_icon(english_name)
    
    html = []
    html.append(f"""
                    <!-- Divider -->
                    <tr>
                        <td class="mobile-padding" style="padding: 0 50px;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="height: 2px; background-color: #e0e0e0;"></td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Category: {category_name} -->
                    <tr>
                        <td class="mobile-padding" style="padding: 40px 50px 25px 50px;">
                            <table cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td valign="middle" style="padding-right: 8px;">
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            {icon}
                                        </svg>
                                    </td>
                                    <td valign="middle">
                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 13px; font-weight: 700; color: #000000; letter-spacing: 2px;">{english_name}</font>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
""")
    
    # 모든 기사 표시 - 작은 썸네일 + 첫 문장
    for idx, a in enumerate(articles):
        padding_bottom = "25px" if idx < len(articles) - 1 else "40px"
        first_sentence = get_first_sentence(a.get('content_summary_kr', ''))
        
        html.append(f"""
                    <tr>
                        <td class="mobile-padding" style="padding: 0 50px {padding_bottom} 50px;">
                            <!--[if mso]>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td width="120" valign="top" style="padding-right: 15px;">
                                        <a href="{escape_html(a.get('url', '#'))}" style="text-decoration: none;">
                                            <img src="{escape_html(a.get('thumbnail', ''))}" width="120" height="80" style="display: block; width: 120px; height: 80px;" alt="{escape_html(a.get('media', ''))}">
                                        </a>
                                    </td>
                                    <td valign="top">
                                        <a href="{escape_html(a.get('url', '#'))}" style="text-decoration: none; color: #000000;">
                                            <div style="padding-bottom: 6px;">
                                                <font face="Malgun Gothic, Arial, sans-serif" style="font-size: 14px; font-weight: 700; color: #000000; line-height: 1.4;">{escape_html(a.get('title_kr', a.get('title', '')))}</font>
                                            </div>
                                            <div style="padding-bottom: 8px;">
                                                <font face="Malgun Gothic, Arial, sans-serif" style="font-size: 12px; font-weight: 400; color: #666666; line-height: 1.5;">{escape_html(first_sentence)}</font>
                                            </div>
                                            <div>
                                                <font face="Malgun Gothic, Arial, sans-serif" style="font-size: 11px; font-weight: 500; color: #999999;">{escape_html(a.get('media', ''))} · {format_date(a.get('date', ''))}</font>
                                            </div>
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <![endif]-->
                            <!--[if !mso]><!-->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td class="news-thumbnail" width="120" style="padding-right: 15px; vertical-align: top;">
                                        <a href="{escape_html(a.get('url', '#'))}" style="text-decoration: none; display: block;">
                                            <img src="{escape_html(a.get('thumbnail', ''))}" width="120" style="display: block; width: 120px; height: 80px; object-fit: cover; background-color: #f0f0f0;" alt="{escape_html(a.get('media', ''))}">
                                        </a>
                                    </td>
                                    <td style="vertical-align: top;">
                                        <a href="{escape_html(a.get('url', '#'))}" style="text-decoration: none; color: inherit; display: block;">
                                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                                <tr>
                                                    <td style="padding-bottom: 6px;">
                                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 14px; font-weight: 700; color: #000000; line-height: 1.4;">{escape_html(a.get('title_kr', a.get('title', '')))}</font>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding-bottom: 8px;">
                                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 12px; font-weight: 400; color: #666666; line-height: 1.5;">{escape_html(first_sentence)}</font>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td>
                                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 11px; font-weight: 500; color: #999999;">{escape_html(a.get('media', ''))} · {format_date(a.get('date', ''))}</font>
                                                    </td>
                                                </tr>
                                            </table>
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <!--<![endif]-->
                        </td>
                    </tr>
""")
    
    return ''.join(html)

def get_first_sentence(text):
    """첫 번째 문장 추출"""
    if not text:
        return ""
    # 마침표, 느낌표, 물음표로 문장 구분
    for delimiter in ['. ', '! ', '? ', '。', '！', '？']:
        if delimiter in text:
            return text.split(delimiter)[0] + delimiter.strip()
    # 구분자가 없으면 전체 텍스트 반환 (최대 100자)
    return text[:100] + ('...' if len(text) > 100 else '')

def generate_ai_summary_section(summary_text):
    """AI Summary 섹션 생성"""
    if not summary_text:
        return ""
    
    # 불릿 포인트 파싱
    bullets = []
    for line in summary_text.split('\n'):
        line = line.strip()
        if line.startswith('•') or line.startswith('-') or line.startswith('*'):
            bullet_text = line.lstrip('•-* ').strip()
            if bullet_text:
                bullets.append(bullet_text)
    
    if not bullets:
        return ""
    
    bullets_html = []
    for bullet in bullets:
        bullets_html.append(f"""
                                        <tr>
                                            <td style="padding: 8px 0;">
                                                <table cellpadding="0" cellspacing="0" border="0">
                                                    <tr>
                                                        <td valign="top" style="padding-right: 12px;">
                                                            <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 16px; font-weight: 700; color: #667eea;">•</font>
                                                        </td>
                                                        <td valign="top">
                                                            <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 14px; font-weight: 400; color: #333333; line-height: 1.6;">{escape_html(bullet)}</font>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>""")
    
    return f"""
                    <!-- AI Summary Section -->
                    <tr>
                        <td class="mobile-padding" style="padding: 40px 50px 10px 50px;">
                            <table cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td valign="middle" style="padding-right: 8px;">
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7zm2.85 11.1l-.85.6V16h-4v-2.3l-.85-.6C7.8 12.16 7 10.63 7 9c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.63-.8 3.16-2.15 4.1z" fill="#000000"/>
                                        </svg>
                                    </td>
                                    <td valign="middle">
                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 13px; font-weight: 700; color: #000000; letter-spacing: 2px;">AI SUMMARY</font>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <tr>
                        <td class="mobile-padding" style="padding: 20px 50px 40px 50px;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8f9fa; border-left: 4px solid #667eea; border-radius: 4px;">
                                <tr>
                                    <td style="padding: 25px 30px;">
                                        <table width="100%" cellpadding="0" cellspacing="0" border="0">
{''.join(bullets_html)}
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
"""

def get_category_icon(english_name):
    """카테고리별 SVG 아이콘 반환 (검은색)"""
    icons = {
        'HOT TREND': '<path d="M13 10V3L4 14h7v7l9-11h-7z" fill="#000000"/>',
        'REGULATION & ISSUES': '<path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" fill="#000000"/>',
        'NEW RELEASES': '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#000000"/>',
        'REVENUE & PERFORMANCE': '<path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z" fill="#000000"/>',
        'UPDATES & PATCHES': '<path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" fill="#000000"/>',
        'IP & COLLABORATIONS': '<path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" fill="#000000"/>',
        'COMMUNITY & EVENTS': '<path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="#000000"/>'
    }
    return icons.get(english_name, '<circle cx="12" cy="12" r="8" fill="#000000"/>')

def generate_compact_category_section(category_name, articles, english_name):
    """간결한 카테고리 섹션 생성 (리스트 형태, 모든 기사 표시)"""
    if not articles:
        return ""
    
    icon = get_category_icon(english_name)
    
    html = []
    html.append(f"""
                    <!-- Divider -->
                    <tr>
                        <td class="mobile-padding" style="padding: 0 50px;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="height: 2px; background-color: #e0e0e0;"></td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Category: {category_name} -->
                    <tr>
                        <td class="mobile-padding" style="padding: 40px 50px 20px 50px;">
                            <table cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td valign="middle" style="padding-right: 8px;">
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            {icon}
                                        </svg>
                                    </td>
                                    <td valign="middle">
                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 13px; font-weight: 700; color: #000000; letter-spacing: 2px;">{english_name}</font>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
""")
    
    # 모든 기사 표시
    for idx, a in enumerate(articles):
        border_style = "border-bottom: 1px solid #e0e0e0;" if idx < len(articles) - 1 else ""
        padding_bottom = "10px" if idx < len(articles) - 1 else "40px"
        first_sentence = get_first_sentence(a.get('content_summary_kr', ''))
        
        html.append(f"""
                    <tr>
                        <td class="mobile-padding" style="padding: 0 50px {padding_bottom} 50px;">
                            <!--[if mso]>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="{border_style}">
                                <tr>
                                    <td style="padding: 12px 0;">
                                        <a href="{escape_html(a.get('url', '#'))}" style="text-decoration: none; color: #000000;">
                                            <div style="padding-bottom: 6px;">
                                                <font face="Malgun Gothic, Arial, sans-serif" style="font-size: 14px; font-weight: 700; color: #000000; line-height: 1.4;">{escape_html(a.get('title_kr', a.get('title', '')))}</font>
                                            </div>
                                            <div>
                                                <font face="Malgun Gothic, Arial, sans-serif" style="font-size: 12px; font-weight: 400; color: #999999;">{escape_html(first_sentence)} · {escape_html(a.get('media', ''))} · {format_date(a.get('date', ''))}</font>
                                            </div>
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <![endif]-->
                            <!--[if !mso]><!-->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="padding: 12px 0; {border_style}">
                                        <a href="{escape_html(a.get('url', '#'))}" style="text-decoration: none; color: inherit; display: block;">
                                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                                <tr>
                                                    <td style="padding-bottom: 6px;">
                                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 14px; font-weight: 700; color: #000000; line-height: 1.4;">{escape_html(a.get('title_kr', a.get('title', '')))}</font>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td>
                                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 12px; font-weight: 400; color: #999999;">{escape_html(first_sentence)} · {escape_html(a.get('media', ''))} · {format_date(a.get('date', ''))}</font>
                                                    </td>
                                                </tr>
                                            </table>
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <!--<![endif]-->
                        </td>
                    </tr>
""")
    
    return ''.join(html)

def generate_html(data):
    """전체 HTML 생성"""
    # 데이터 구조 확인
    if isinstance(data, dict):
        daily_summary = data.get('daily_summary', '')
        articles = data.get('articles', [])
    else:
        daily_summary = ''
        articles = data
    
    # 필터링
    filtered = filter_articles(articles)
    print(f">> game_relevance >= 0.5 AND importance >= 0.4 필터링: {len(filtered)}개 기사")
    
    # HOT TREND
    hot_articles = get_hot_trend_articles(filtered)
    print(f">> HOT TREND (댓글 10개 이상): {len(hot_articles)}개 기사")
    
    # HOT TREND에 포함된 기사 제외
    hot_urls = {a['url'] for a in hot_articles[:5]}
    remaining = [a for a in filtered if a['url'] not in hot_urls]
    
    # 카테고리 분류
    categories = categorize_articles(remaining)
    
    # 현재 날짜
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    date_str = now.strftime('%Y.%m.%d')
    day_str = now.strftime('%A')
    
    # HTML 생성
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>글로벌 게임 데일리 뉴스레터</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td, a {{ font-family: 'Malgun Gothic', Arial, sans-serif !important; }}
    </style>
    <![endif]-->
    <style>
        @media only screen and (max-width: 1000px) {{
            .container {{ width: 100% !important; }}
            .mobile-padding {{ padding-left: 20px !important; padding-right: 20px !important; }}
            .two-col-left, .two-col-right {{ width: 100% !important; display: block !important; padding: 0 !important; margin-bottom: 20px !important; }}
            .news-thumbnail {{ width: 120px !important; }}
            div[style*="display: flex"] {{ display: block !important; }}
            div[style*="flex: 1"] {{ width: 100% !important; margin-bottom: 20px !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: 'Malgun Gothic', '맑은 고딕', 'Apple SD Gothic Neo', Arial, sans-serif; background-color: #ffffff;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff">
        <tr>
            <td align="center" style="padding: 0;">
                <!-- Main Container -->
                <table class="container" width="1000" cellpadding="0" cellspacing="0" border="0" style="max-width: 1000px;">
                    
                    <!-- Header -->
                    <tr>
                        <td class="mobile-padding" style="padding: 60px 50px 20px 50px;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td align="left" style="padding-bottom: 8px;">
                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 48px; font-weight: 900; color: #000000; letter-spacing: -2px; line-height: 1;">Daily Game</font>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="left" style="padding-bottom: 12px;">
                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 14px; font-weight: 400; color: #999999;">{date_str} — {day_str} Edition</font>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="left">
                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 12px; font-weight: 400; color: #666666; font-style: italic;">새 아웃룩 또는 모바일 보기에 최적화 되어 있습니다.</font>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Thick Divider -->
                    <tr>
                        <td class="mobile-padding" style="padding: 0 50px;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="height: 4px; background-color: #000000;"></td>
                                </tr>
                            </table>
                        </td>
                    </tr>

{generate_ai_summary_section(daily_summary)}

                    <!-- HOT TREND Section -->
                    <tr>
                        <td class="mobile-padding" style="padding: 40px 50px 10px 50px;">
                            <table cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td valign="middle" style="padding-right: 8px;">
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            {get_category_icon('HOT TREND')}
                                        </svg>
                                    </td>
                                    <td valign="middle">
                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 13px; font-weight: 700; color: #000000; letter-spacing: 2px;">HOT TREND</font>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

{generate_hot_section(hot_articles[:5])}

{generate_category_section('규제 & 이슈', categories['규제 & 이슈'], 'REGULATION & ISSUES')}

{generate_category_section('게임 출시 & 발표', categories['게임 출시 & 발표'], 'NEW RELEASES')}

{generate_compact_category_section('매출 & 성과', categories['매출 & 성과'], 'REVENUE & PERFORMANCE')}

{generate_compact_category_section('업데이트 & 패치', categories['업데이트 & 패치'], 'UPDATES & PATCHES')}

{generate_compact_category_section('IP & 콜라보', categories['IP & 콜라보'], 'IP & COLLABORATIONS')}

{generate_compact_category_section('커뮤니티 & 이벤트', categories['커뮤니티 & 이벤트'], 'COMMUNITY & EVENTS')}

                    <!-- Footer -->
                    <tr>
                        <td class="mobile-padding" style="padding: 40px 50px 60px 50px; border-top: 4px solid #000000;">
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td align="center" style="padding-bottom: 10px;">
                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 11px; font-weight: 400; color: #999999; line-height: 1.6;">Sources: IGN, GameSpot, Gamelook</font>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center">
                                        <font face="'Malgun Gothic', '맑은 고딕', Arial, sans-serif" style="font-size: 10px; font-weight: 400; color: #cccccc;">© 2025 Daily Game Report</font>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
    
    return html

def main():
    print("=" * 70)
    print("HTML 뉴스레터 생성 시작")
    print("=" * 70)
    
    # 데이터 로드
    data = load_articles()
    if not data:
        print("[ERROR] 기사 데이터가 없습니다.")
        return
    
    # 데이터 구조 확인
    if isinstance(data, dict):
        articles = data.get('articles', [])
        print(f">> 총 {len(articles)}개 기사 로드")
        if data.get('daily_summary'):
            print(f">> AI Summary 포함")
    else:
        articles = data
        print(f">> 총 {len(articles)}개 기사 로드")
    
    # HTML 생성
    html_content = generate_html(data)
    
    # 파일 저장
    output_file = 'daily_newsletter.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n[OK] HTML 뉴스레터 생성 완료: {output_file}")
    print("=" * 70)

if __name__ == '__main__':
    main()

