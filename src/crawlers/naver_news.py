import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
# pandas 의존성 제거
import time
import random

class NaverNewsCrawler:
    """네이버 뉴스 크롤러 클래스"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.categories = {
            '정치': 100,
            '경제': 101,
            '사회': 102,
            '생활/문화': 103,
            'IT/과학': 105,
            '세계': 104
        }
    
    def get_news_list(self, category_name, page=1, date=None):
        """
        특정 카테고리의 뉴스 목록을 가져옵니다.
        
        Args:
            category_name (str): 카테고리 이름 ('정치', '경제', '사회', '생활/문화', 'IT/과학', '세계')
            page (int): 페이지 번호
            date (str): 날짜 (YYYYMMDD 형식, 기본값은 오늘)
            
        Returns:
            list: 뉴스 기사 목록 (제목, URL, 언론사, 요약, 날짜)
        """
        if category_name not in self.categories:
            raise ValueError(f"유효한 카테고리가 아닙니다. 가능한 카테고리: {list(self.categories.keys())}")
        
        category_id = self.categories[category_name]
        
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        url = f"https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1={category_id}&date={date}&page={page}"
        
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        # 뉴스 목록 추출
        news_items = soup.select('.list_body .type06_headline li, .list_body .type06 li')
        
        for item in news_items:
            try:
                title_tag = item.select_one('dt:not(.photo) a, dt.photo a')
                title = title_tag.text.strip()
                link = title_tag['href']
                
                # 언론사 추출
                press = item.select_one('.writing').text.strip()
                
                # 요약 추출
                summary = item.select_one('.lede').text.strip()
                
                # 날짜 추출
                date_str = item.select_one('.date').text.strip()
                
                news_list.append({
                    'title': title,
                    'url': link,
                    'press': press,
                    'summary': summary,
                    'date': date_str,
                    'category': category_name
                })
            except Exception as e:
                print(f"기사 파싱 중 오류 발생: {e}")
                continue
        
        return news_list
    
    def extract_keywords(self, text, top_n=10):
        """
        텍스트에서 키워드를 추출합니다.
        
        Args:
            text (str): 키워드를 추출할 텍스트
            top_n (int): 추출할 키워드 수
            
        Returns:
            list: 키워드 목록
        """
        # 간단한 키워드 추출 로직 (실제로는 더 복잡한 알고리즘 사용 필요)
        # 불용어 목록
        stopwords = ['있다', '하다', '이다', '되다', '않다', '그', '및', '등', '를', '을', '이', '가', '의', '에', '로', '으로']
        
        # 특수문자 및 숫자 제거
        clean_text = re.sub(r'[^\w\s]', '', text)
        clean_text = re.sub(r'\d+', '', clean_text)
        
        # 단어 분리
        words = clean_text.split()
        
        # 불용어 제거 및 단어 길이 필터링
        filtered_words = [word for word in words if word not in stopwords and len(word) > 1]
        
        # 단어 빈도수 계산
        word_freq = {}
        for word in filtered_words:
            if word in word_freq:
                word_freq[word] += 1
            else:
                word_freq[word] = 1
        
        # 빈도수 기준 상위 키워드 추출
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_words[:top_n]]
    
    def get_trending_keywords(self, categories=None, pages_per_category=2, top_n=20):
        """
        여러 카테고리에서 트렌드 키워드를 추출합니다.
        
        Args:
            categories (list): 크롤링할 카테고리 목록 (기본값: 모든 카테고리)
            pages_per_category (int): 각 카테고리별로 크롤링할 페이지 수
            top_n (int): 반환할 상위 키워드 수
            
        Returns:
            dict: 카테고리별 트렌드 키워드 및 전체 트렌드 키워드
        """
        if categories is None:
            categories = list(self.categories.keys())
        
        all_news = []
        all_text = ""
        
        for category in categories:
            for page in range(1, pages_per_category + 1):
                try:
                    news_list = self.get_news_list(category, page)
                    all_news.extend(news_list)
                    
                    # 텍스트 누적
                    for news in news_list:
                        all_text += news['title'] + " " + news['summary'] + " "
                    
                    # 과도한 요청 방지를 위한 딜레이
                    time.sleep(random.uniform(1.0, 2.0))
                except Exception as e:
                    print(f"{category} 카테고리 {page} 페이지 크롤링 중 오류: {e}")
        
        # 전체 키워드 추출
        overall_keywords = self.extract_keywords(all_text, top_n)
        
        # 카테고리별 키워드 추출
        category_keywords = {}
        for category in categories:
            category_news = [news for news in all_news if news['category'] == category]
            category_text = " ".join([news['title'] + " " + news['summary'] for news in category_news])
            category_keywords[category] = self.extract_keywords(category_text, top_n=10)
        
        return {
            'overall': overall_keywords,
            'by_category': category_keywords,
            'news_data': all_news
        }


# 테스트 코드
if __name__ == "__main__":
    crawler = NaverNewsCrawler()
    trends = crawler.get_trending_keywords(pages_per_category=1)
    print("전체 트렌드 키워드:", trends['overall'])
    
    for category, keywords in trends['by_category'].items():
        print(f"{category} 카테고리 키워드:", keywords)
