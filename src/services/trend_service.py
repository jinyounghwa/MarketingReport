from src.crawlers import NaverNewsCrawler, NaverBlogCrawler, DaumNewsCrawler, DaumBlogCrawler
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import threading
import time
import re
# pandas 의존성 제거

class TrendService:
    """트렌드 데이터를 수집하고 관리하는 서비스 클래스"""
    
    def __init__(self, data_dir=None):
        """
        TrendService 초기화
        
        Args:
            data_dir (str): 데이터를 저장할 디렉토리 경로 (기본값: 프로젝트 루트의 data 디렉토리)
        """
        if data_dir is None:
            self.data_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / 'data'
        else:
            self.data_dir = Path(data_dir)
        
        # 데이터 디렉토리가 없으면 생성
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 크롤러 초기화
        self.naver_news_crawler = NaverNewsCrawler()
        self.naver_blog_crawler = NaverBlogCrawler()
        self.daum_news_crawler = DaumNewsCrawler()
        self.daum_blog_crawler = DaumBlogCrawler()
        
        # 최근 수집 데이터 캐시
        self.recent_data = None
        self.last_collected = None
        
        # 백그라운드 수집 스레드
        self.collection_thread = None
        self.is_collecting = False
    
    def _get_data_path(self, date_str=None):
        """
        특정 날짜의 데이터 파일 경로를 반환합니다.
        
        Args:
            date_str (str): 날짜 문자열 (YYYY-MM-DD 형식, 기본값: 오늘)
            
        Returns:
            Path: 데이터 파일 경로
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        return self.data_dir / f"trends_{date_str}.json"
    
    def collect_trends(self, categories=None, keywords=None, save=True, sources=None):
        """
        트렌드 데이터를 수집합니다.
        
        Args:
            categories (list): 수집할 뉴스 카테고리 목록 (기본값: 모든 카테고리)
            keywords (list): 수집할 블로그 키워드 목록 (기본값: 뉴스에서 추출한 상위 키워드)
            save (bool): 수집한 데이터를 파일로 저장할지 여부
            sources (list): 사용할 데이터 소스 (기본값: ['naver', 'daum'])
            
        Returns:
            dict: 수집한 트렌드 데이터
        """
        if sources is None:
            sources = ['naver', 'daum']
            
        all_news_data = []
        all_news_keywords = []
        all_blog_data = []
        category_keywords = {}
        
        # 네이버 뉴스 수집
        if 'naver' in sources:
            print("\n네이버 뉴스 수집 중...")
            naver_news_trends = self.naver_news_crawler.get_trending_keywords(categories=categories, pages_per_category=2)
            all_news_data.extend(naver_news_trends['news_data'])
            all_news_keywords.extend(naver_news_trends['overall'])
            
            # 카테고리별 키워드 통합
            for category, keywords_list in naver_news_trends['by_category'].items():
                if category not in category_keywords:
                    category_keywords[category] = []
                category_keywords[category].extend(keywords_list)
        
        # 다음 뉴스 수집
        if 'daum' in sources:
            print("\n다음 뉴스 수집 중...")
            daum_news_trends = self.daum_news_crawler.get_trending_keywords(categories=categories, pages_per_category=2)
            all_news_data.extend(daum_news_trends['news_data'])
            all_news_keywords.extend(daum_news_trends['overall'])
            
            # 카테고리별 키워드 통합
            for category, keywords_list in daum_news_trends['by_category'].items():
                if category not in category_keywords:
                    category_keywords[category] = []
                category_keywords[category].extend(keywords_list)
        
        # 키워드 빈도수 계산
        keyword_freq = {}
        for keyword in all_news_keywords:
            if keyword in keyword_freq:
                keyword_freq[keyword] += 1
            else:
                keyword_freq[keyword] = 1
        
        # 빈도수 기준 상위 키워드 추출
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        top_keywords = [keyword for keyword, freq in sorted_keywords[:20]]
        
        # 키워드가 지정되지 않은 경우 뉴스에서 추출한 키워드 사용
        if keywords is None:
            keywords = top_keywords[:5]  # 상위 5개 키워드만 사용
        
        # 블로그 데이터 수집
        if 'naver' in sources:
            print("\n네이버 블로그 수집 중...")
            naver_blog_trends = self.naver_blog_crawler.get_trending_blogs(keywords, pages_per_keyword=1)
            all_blog_data.extend(naver_blog_trends['all_blogs'])
        
        if 'daum' in sources:
            print("\n다음 블로그 수집 중...")
            daum_blog_trends = self.daum_blog_crawler.get_trending_blogs(keywords, pages_per_keyword=1)
            all_blog_data.extend(daum_blog_trends['all_blogs'])
        
        # 카테고리별 키워드 중복 제거
        for category in category_keywords:
            unique_keywords = []
            seen = set()
            for keyword in category_keywords[category]:
                if keyword not in seen:
                    seen.add(keyword)
                    unique_keywords.append(keyword)
            category_keywords[category] = unique_keywords[:10]  # 상위 10개만 유지
        
        # 결과 데이터 구성
        trend_data = {
            'collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'news_trends': {
                'news_data': all_news_data,
                'by_category': category_keywords,
                'overall': top_keywords
            },
            'blog_trends': {
                'all_blogs': all_blog_data
            },
            'top_keywords': top_keywords[:10],  # 상위 10개 키워드
            'sources': sources
        }
        
        # 데이터 캐싱
        self.recent_data = trend_data
        self.last_collected = datetime.now()
        
        # 파일로 저장
        if save:
            data_path = self._get_data_path()
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(trend_data, f, ensure_ascii=False, indent=2)
        
        return trend_data
    
    def get_trends(self, date_str=None, force_collect=False):
        """
        특정 날짜의 트렌드 데이터를 가져옵니다.
        
        Args:
            date_str (str): 날짜 문자열 (YYYY-MM-DD 형식, 기본값: 오늘)
            force_collect (bool): 데이터가 없거나 오래된 경우 강제로 수집할지 여부
            
        Returns:
            dict: 트렌드 데이터
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 오늘 데이터를 요청하고 캐시된 데이터가 있는 경우
        if date_str == datetime.now().strftime('%Y-%m-%d') and self.recent_data is not None:
            # 마지막 수집 후 1시간이 지나지 않았으면 캐시된 데이터 반환
            if self.last_collected and (datetime.now() - self.last_collected).seconds < 3600:
                return self.recent_data
        
        # 파일에서 데이터 로드
        data_path = self._get_data_path(date_str)
        if data_path.exists():
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 데이터가 없고 강제 수집이 활성화된 경우
        if force_collect and date_str == datetime.now().strftime('%Y-%m-%d'):
            return self.collect_trends()
        
        # 데이터가 없는 경우
        return {
            'error': f"{date_str} 날짜의 트렌드 데이터가 없습니다. 데이터 수집을 먼저 실행해주세요."
        }
    
    def start_background_collection(self, interval_hours=3):
        """
        백그라운드에서 주기적으로 트렌드 데이터를 수집합니다.
        
        Args:
            interval_hours (int): 수집 간격 (시간 단위)
        """
        if self.is_collecting:
            return False
        
        def collection_task():
            self.is_collecting = True
            while self.is_collecting:
                try:
                    self.collect_trends()
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 트렌드 데이터 수집 완료")
                except Exception as e:
                    print(f"트렌드 데이터 수집 중 오류 발생: {e}")
                
                # 다음 수집 시간까지 대기
                for _ in range(interval_hours * 60 * 60):
                    if not self.is_collecting:
                        break
                    time.sleep(1)
        
        self.collection_thread = threading.Thread(target=collection_task)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        
        return True
    
    def stop_background_collection(self):
        """백그라운드 수집을 중지합니다."""
        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=1)
        return True
    
    def get_economy_report(self, date_str=None, include_global=True):
        """
        경제 분야 리포트 데이터를 생성합니다.
        
        Args:
            date_str (str): 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)
            include_global (bool): 세계 경제 포함 여부
            
        Returns:
            dict: 경제 분야 리포트 데이터
        """
        # 항상 오늘 날짜만 사용
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 데이터 가져오기
        trends_data = self.get_trends(date_str)
        
        # 데이터가 없는 경우
        if 'error' in trends_data:
            return {
                'error': trends_data['error'],
                'date': date_str
            }
        
        # 경제 관련 뉴스 필터링
        economy_news = []
        global_economy_news = []
        
        # 뉴스 데이터가 있는지 확인
        if 'news_data' in trends_data['news_trends']:
            for news in trends_data['news_trends']['news_data']:
                # 카테고리 필드가 있는지 확인
                category = news.get('category', '')
                source = news.get('source', 'unknown')
                
                # 경제 뉴스 추출
                if category == '경제' or '경제' in news.get('title', ''):
                    economy_news.append(news)
                # 세계 경제 뉴스 추출
                elif include_global and (category == '세계' or category == '국제') and self._is_economy_related(news.get('title', '')):
                    global_economy_news.append(news)
        
        # 경제 관련 키워드 추출
        all_economy_text = ""
        for news in economy_news + global_economy_news:
            all_economy_text += news.get('title', '') + " " + news.get('summary', '') + " "
        
        # 경제 키워드 추출 (텍스트가 없으면 기본 키워드 사용)
        if all_economy_text.strip():
            economy_keywords = self._extract_keywords(all_economy_text, 20)
        else:
            economy_keywords = [
                '경제', '금융', '주식', '상승', '하락', '환율', '금리',
                '물가', '인플레이션', '재테크', '투자', '시장', '무역',
                '기업', '산업', '고용', 'GDP', '경제성장', '중앙은행'
            ]
        
        # 경제 관련 블로그 필터링
        economy_blogs = []
        
        # 블로그 데이터가 있는지 확인
        if 'all_blogs' in trends_data['blog_trends']:
            for blog in trends_data['blog_trends']['all_blogs']:
                if self._is_economy_related(blog.get('title', '')) or any(keyword in blog.get('title', '') for keyword in economy_keywords[:10]):
                    economy_blogs.append(blog)
        
        # 결과 데이터 구성
        return {
            'date': date_str,
            'collection_time': trends_data.get('collection_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'economy_keywords': economy_keywords,
            'domestic_economy_news': economy_news,
            'global_economy_news': global_economy_news,
            'economy_blogs': economy_blogs,
            'sources': trends_data.get('sources', ['naver', 'daum'])
        }
    
    def _is_economy_related(self, text):
        """
        텍스트가 경제 관련인지 확인합니다.
        
        Args:
            text (str): 확인할 텍스트
            
        Returns:
            bool: 경제 관련 여부
        """
        economy_keywords = [
            '경제', '금융', '주식', '상승', '하락', '원화', '달러', '환율',
            '금리', '인플레', '인플레이션', '디플레', '디플레이션', '물가',
            '재테크', '재무', '투자', '시장', '무역', '수출', '수입', '관세',
            '환율', '상품', '사업', '기업', '산업', '일자리', '고용', '실업',
            'GDP', '국내총생산', '경제성장', '경제위기', '경제정책', '기준금리',
            '중앙은행', '세금', '세제', '세수', '세정', '예산', '부채', '국채'
        ]
        
        return any(keyword in text for keyword in economy_keywords)
    
    def _extract_keywords(self, text, top_n=10):
        """
        텍스트에서 키워드를 추출합니다.
        
        Args:
            text (str): 키워드를 추출할 텍스트
            top_n (int): 추출할 키워드 수
            
        Returns:
            list: 키워드 목록
        """
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
        
    def get_weekly_report(self, end_date=None):
        """
        주간 리포트 데이터를 생성합니다.
        
        Args:
            end_date (str): 종료 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)
            
        Returns:
            dict: 주간 리포트 데이터
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        start_date_obj = end_date_obj - timedelta(days=6)  # 7일간의 데이터
        
        daily_data = {}
        all_keywords = []
        
        # 각 날짜별 데이터 수집
        current_date = start_date_obj
        while current_date <= end_date_obj:
            date_str = current_date.strftime('%Y-%m-%d')
            data = self.get_trends(date_str)
            
            if 'error' not in data:
                daily_data[date_str] = data
                all_keywords.extend(data.get('top_keywords', []))
            
            current_date += timedelta(days=1)
        
        # 키워드 빈도수 계산
        keyword_freq = {}
        for keyword in all_keywords:
            if keyword in keyword_freq:
                keyword_freq[keyword] += 1
            else:
                keyword_freq[keyword] = 1
        
        # 빈도수 기준 상위 키워드 추출
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        top_weekly_keywords = [keyword for keyword, freq in sorted_keywords[:20]]
        
        return {
            'period': {
                'start': start_date_obj.strftime('%Y-%m-%d'),
                'end': end_date_obj.strftime('%Y-%m-%d')
            },
            'top_keywords': top_weekly_keywords,
            'daily_data': daily_data
        }


# 테스트 코드
if __name__ == "__main__":
    service = TrendService()
    trends = service.collect_trends()
    print(f"수집 시간: {trends['collection_time']}")
    print(f"상위 키워드: {trends['top_keywords']}")
