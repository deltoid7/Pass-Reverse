import requests
from io import BytesIO

def solve_captcha(captcha_content):
    try:
        files = {
            'file': ('captcha.png', BytesIO(captcha_content), 'image/png')
        }
        response = requests.post("https://pass-captcha-solver.onrender.com/predict", files=files)
        if response.status_code == 200:
            data = response.json()
            captcha_answer = data.get('number', 'N/A')
            # print(captcha_answer)
            return captcha_answer
        else:
            return "FAILED"
    except Exception as e:
        print(f"캡차 해결 중 오류: {e}")
        return "FAILED"