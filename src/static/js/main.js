// DOM이 완전히 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // 급상승 키워드 애니메이션 효과
    const trendingItems = document.querySelectorAll('.alert-warning');
    trendingItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.1}s`;
        item.classList.add('fade-in');
    });

    // 카드 호버 효과
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 6px 12px rgba(0,0,0,.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });

    // 토스트 알림 초기화
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    const toastList = toastElList.map(function(toastEl) {
        return new bootstrap.Toast(toastEl, {
            autohide: true,
            delay: 3000
        });
    });
});

// API 호출 함수 예시
async function fetchTrendingKeywords() {
    try {
        const response = await fetch('/api/trends');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('트렌드 키워드를 가져오는 중 오류 발생:', error);
        return [];
    }
}

// 페이지 로드 시 트렌드 키워드 가져오기
window.addEventListener('load', async () => {
    const keywords = await fetchTrendingKeywords();
    // 여기서 키워드를 화면에 표시하는 로직을 추가할 수 있습니다.
});

// 토스트 메시지 표시 함수
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 3000
    });
    bsToast.show();
    
    // 토스트가 사라진 후 DOM에서 제거
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}
