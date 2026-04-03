# PASS용 캡차 솔버
https://github.com/WooilJeong/CaptchaCracker/ 를 수정한 `captcha_cracker_ll.py`가 포함되어 있습니다.<br>
[예시 캡차 이미지](https://github.com/PASS-REVERSE/PASS-Captcha-Solver/blob/main/captcha.png)
```py
import requests
import sys
import os

BASE_URL = "https://pass-captcha-solver.onrender.com/"
image_path = sys.argv[1] if len(sys.argv) > 1 else "captcha.png"

if not os.path.exists(image_path):
    print(f"이미지 파일을 찾을 수 없습니다: {image_path}")
    sys.exit(1)

try:
    with open(image_path, 'rb') as f:
        files = {'file': (os.path.basename(image_path), f, 'image/png')}
        response = requests.post(f"{BASE_URL}/predict", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"캡차 번호: {data.get('number', 'N/A')}")
    else:
        print("서버가 열려있지 않거나 모델이 준비되지 않았습니다")
except:
    print("서버가 열려있지 않거나 모델이 준비되지 않았습니다")
```

<br>

# 권장 방법
무료로 본인용 서버 생성하기<br>
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/PASS-REVERSE/PASS-Captcha-Solver)

그리고 서버 계속 깨어있게 하기 (무료티어는 15분동안 요청 없으면 서버 잠듦)<br>
https://uptimerobot.com/<br>
https://cron-job.org/
