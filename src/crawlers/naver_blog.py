import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time
import random

class NaverBlogCrawler:
    """네이버 블로그 크롤러 클래스"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def search_blogs(self, keyword, start_page=1, end_page=2):
        """
        키워드로 네이버 블로그를 검색합니다.
        
        Args:
            keyword (str): 검색할 키워드
            start_page (int): 시작 페이지
            end_page (int): 종료 페이지
            
        Returns:
            list: 블로그 포스트 목록 (제목, URL, 작성자, 요약, 날짜)
        """
        blog_posts = []
        
        for page in range(start_page, end_page + 1):
            start = (page - 1) * 10 + 1
            url = f"https://search.naver.com/search.naver?where=blog&sm=tab_pge&query={keyword}&start={start}"
            
            try:
                response = requests.get(url, headers=self.headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 블로그 포스트 목록 추출
                blog_items = soup.select('.sh_blog_top')
                
                for item in blog_items:
                    try:
                        title_tag = item.select_one('.sh_blog_title')
                        title = title_tag.text.strip()
                        link = title_tag['href']
                        
                        # 작성자 추출
                        author = item.select_one('.sh_blog_name').text.strip()
                        
                        # 요약 추출
                        summary = item.select_one('.sh_blog_passage').text.strip()
                        
                        # 날짜 추출
                        date_str = item.select_one('.txt_inline').text.strip()
                        
                        blog_posts.append({
                            'title': title,
                            'url': link,
                            'author': author,
                            'summary': summary,
                            'date': date_str,
                            'keyword': keyword
                        })
                    except Exception as e:
                        print(f"블로그 포스트 파싱 중 오류 발생: {e}")
                        continue
                
                # 과도한 요청 방지를 위한 딜레이
                time.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                print(f"블로그 검색 중 오류 발생: {e}")
                continue
        
        return blog_posts
    
    def get_trending_blogs(self, keywords, pages_per_keyword=2):
        """
        여러 키워드에 대한 블로그 포스트를 수집합니다.
        
        Args:
            keywords (list): 검색할 키워드 목록
            pages_per_keyword (int): 각 키워드별로 검색할 페이지 수
            
        Returns:
            dict: 키워드별 블로그 포스트 및 전체 블로그 포스트
        """
        all_blogs = []
        keyword_blogs = {}
        
        for keyword in keywords:
            try:
                blogs = self.search_blogs(keyword, start_page=1, end_page=pages_per_keyword)
                all_blogs.extend(blogs)
                keyword_blogs[keyword] = blogs
                
                # 과도한 요청 방지를 위한 딜레이
                time.sleep(random.uniform(2.0, 3.0))
            except Exception as e:
                print(f"{keyword} 키워드 검색 중 오류: {e}")
        
        return {
            'all_blogs': all_blogs,
            'by_keyword': keyword_blogs
        }


# 테스트 코드
if __name__ == "__main__":
    crawler = NaverBlogCrawler()
    keywords = ["AI 기술", "디지털 마케팅", "빅데이터"]
    blogs = crawler.get_trending_blogs(keywords, pages_per_keyword=1)
    
    print(f"총 {len(blogs['all_blogs'])}개의 블로그 포스트를 수집했습니다.")
    
    for keyword, posts in blogs['by_keyword'].items():
        print(f"{keyword} 키워드 관련 블로그: {len(posts)}개")
