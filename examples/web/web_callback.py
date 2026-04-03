# Flask 로깅 끄는 부분 삭제해도 무방
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from flask import Flask, request, render_template_string
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from pass_reverse.gui import app as auth_app, decrypt_user_data

SECRET_KEY = 'your_secret'
PORT = 3000

# 인증앱 설정
auth_app.secret_key = SECRET_KEY
auth_app.config['PASS_SUCCESS_REDIRECT'] = f'http://localhost:{PORT}/callback'
# auth_app.config['CP_DATA_URL'] = '' # 기본값: https://knvd.krcert.or.kr/api/core/pu/common/nice/get

# 클라이언트 앱
app = Flask(__name__)

INDEX_HTML = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>내 서비스</title>
</head>
<body>
    <a href="/auth/">인증하기</a>
</body>
</html>
'''

SUCCESS_HTML = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>인증 결과 확인</title>
</head>
<body>
    <div class="result-box">
        <h2>인증 정보 결과</h2>
        <div class="result-item">
            <span class="result-label">통신사:</span>
            <span class="result-value">{{ isp }} ({{ isp_code }})</span>
        </div>
        <div class="result-item">
            <span class="result-label">인증방식:</span>
            <span class="result-value">{{ cert_method }}</span>
        </div>
        <div class="result-item">
            <span class="result-label">이름:</span>
            <span class="result-value">{{ user_name }}</span>
        </div>
        <div class="result-item">
            <span class="result-label">휴대폰 번호:</span>
            <span class="result-value">{{ mobile_no }}</span>
        </div>
        <div class="result-item">
            <span class="result-label">생년월일:</span>
            <span class="result-value">{{ birth_date }}</span>
        </div>
        <br>
        <button onclick="location.href='/'" class="btn_pass show">처음으로</button>
    </div>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)


@app.route('/callback')
def callback():
    token = request.args.get('token')
    if not token:
        return "토큰이 없습니다.", 400
    
    try:
        user_info = decrypt_user_data(token, SECRET_KEY)
    except Exception as e:
        return f"토큰 복호화 실패: {e}", 400
    
    return render_template_string(
        SUCCESS_HTML,
        user_name=user_info.get('user_name'),
        mobile_no=user_info.get('mobile_no'),
        isp=user_info.get('isp'),
        isp_code=user_info.get('isp_code'),
        cert_method=user_info.get('cert_method'),
        birth_date=user_info.get('birth_date')
    )

app = DispatcherMiddleware(app, {
    '/auth': auth_app
})


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    
    print(f"서버 시작: http://localhost:{PORT}")
    print(f"  - 클라이언트: http://localhost:{PORT}/")
    print(f"  - 인증: http://localhost:{PORT}/auth/")
    
    run_simple('0.0.0.0', PORT, app, use_reloader=False, use_debugger=False)
