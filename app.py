from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime, timedelta
import os
from pathlib import Path
from dotenv import load_dotenv
from src.services import TrendService

# 환경 변수 로드
load_dotenv()

# 템플릿 폴더 경로 설정
BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / 'src' / 'templates'
STATIC_DIR = BASE_DIR / 'src' / 'static'
DATA_DIR = BASE_DIR / 'data'

app = Flask(__name__, 
           template_folder=str(TEMPLATE_DIR),
           static_folder=str(STATIC_DIR))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# 트렌드 서비스 초기화
trend_service = TrendService(data_dir=DATA_DIR)

# 루트 경로 - 대시보드
@app.route('/')
def index():
    # 최신 트렌드 데이터 가져오기
    trends = trend_service.get_trends()
    
    # 데이터가 없는 경우 빈 데이터 사용
    if 'error' in trends:
        trends = {
            'top_keywords': [],
            'news_trends': {'by_category': {}},
            'collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    return render_template('index.html', trends=trends)

# 트렌드 리포트 페이지
@app.route('/trends')
def trends_page():
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    category = request.args.get('category', 'all')
    
    # 트렌드 데이터 가져오기
    trends = trend_service.get_trends(date_str)
    
    # 데이터가 없는 경우 오류 표시
    if 'error' in trends:
        return render_template('trends.html', error=trends['error'], date=date_str)
    
    return render_template('trends.html', trends=trends, date=date_str, category=category)

# 경제 리포트 페이지
@app.route('/economy')
def economy_report():
    include_global = request.args.get('include_global', 'on') == 'on'
    
    # 경제 리포트 데이터 가져오기 (항상 오늘 날짜 사용)
    report = trend_service.get_economy_report(include_global=include_global)
    
    return render_template('economy.html', report=report, include_global=include_global)

# 주간 리포트 페이지
@app.route('/weekly')
def weekly_report():
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # 주간 리포트 데이터 가져오기
    report = trend_service.get_weekly_report(end_date)
    
    return render_template('weekly.html', report=report)

# 데이터 수집 경로
@app.route('/collect', methods=['GET', 'POST'])
def collect_data():
    if request.method == 'POST':
        try:
            # 데이터 수집 시작
            trends = trend_service.collect_trends()
            return jsonify({
                'success': True,
                'message': f"데이터 수집 완료: {trends['collection_time']}",
                'collection_time': trends['collection_time']
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f"데이터 수집 중 오류 발생: {str(e)}"
            }), 500
    
    return render_template('collect.html')

# 네비게이션 바
@app.route('/nav')
def nav():
    return render_template('nav.html')

# API 라우트 - 트렌드 데이터
@app.route('/api/trends', methods=['GET'])
def get_trends_api():
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    category = request.args.get('category', 'all')
    
    # 트렌드 데이터 가져오기
    trends = trend_service.get_trends(date_str)
    
    # 데이터가 없는 경우 오류 반환
    if 'error' in trends:
        return jsonify({
            'success': False,
            'message': trends['error']
        }), 404
    
    # 특정 카테고리만 필터링
    if category != 'all' and 'news_trends' in trends and 'by_category' in trends['news_trends']:
        if category in trends['news_trends']['by_category']:
            filtered_trends = {
                'collection_time': trends['collection_time'],
                'top_keywords': trends['news_trends']['by_category'][category],
                'category': category
            }
            return jsonify(filtered_trends)
    
    return jsonify(trends)

# API 라우트 - 경제 리포트
@app.route('/api/economy', methods=['GET'])
def get_economy_report_api():
    include_global = request.args.get('include_global', 'true').lower() == 'true'
    
    # 경제 리포트 데이터 가져오기 (항상 오늘 날짜 사용)
    report = trend_service.get_economy_report(include_global=include_global)
    
    return jsonify(report)

# API 라우트 - 주간 리포트
@app.route('/api/weekly', methods=['GET'])
def get_weekly_report_api():
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # 주간 리포트 데이터 가져오기
    report = trend_service.get_weekly_report(end_date)
    
    return jsonify(report)

# API 라우트 - 데이터 수집
@app.route('/api/collect', methods=['POST'])
def collect_data_api():
    try:
        # 데이터 수집 시작
        trends = trend_service.collect_trends()
        return jsonify({
            'success': True,
            'message': f"데이터 수집 완료: {trends['collection_time']}",
            'collection_time': trends['collection_time']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"데이터 수집 중 오류 발생: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
