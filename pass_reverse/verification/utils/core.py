import requests
import re
import random
import uuid
import sys
from bs4 import BeautifulSoup
import time

DEFAULT_CP_DATA_URL = 'https://knvd.krcert.or.kr/api/core/pu/common/nice/get'

def get_captcha_image(session, captcha_version):
    response = session.get(f'https://nice.checkplus.co.kr/cert/captcha/image/{captcha_version}')
    return response.content

def extract_captcha_version(response_text):
    match = re.search(r'const\s+captchaVersion\s*=\s*"([^"]+)"', response_text)
    if match:
        return match.group(1)
    return None

def save_captcha_image(captcha_content, filename):
    with open(filename, 'wb') as f:
        f.write(captcha_content)

def process_captcha_authentication(session, response_text, captcha_mode='auto', captcha_input_callback=None):
    captcha_version = extract_captcha_version(response_text)
    if not captcha_version:
        return None
    
    captcha_content = get_captcha_image(session, captcha_version)
    
    if captcha_mode == 'auto':
        try:
            from pass_reverse.verification.utils.captcha_solver import solve_captcha
            result = solve_captcha(captcha_content)
            if result != "FAILED":
                return result
        except (ImportError, Exception):
            pass
            
    if captcha_input_callback:
        return captcha_input_callback(captcha_content, "보안문자를 입력해주세요.")
    
    return None

def wait_for_confirm(session, acc_tk_service_info, method, progress_callback=None):
    while True:
        res = session.post(
            url='https://nice.checkplus.co.kr/cert/polling/confirm/check/proc',
            headers={
                "X-Requested-With": "XMLHTTPRequest",
                "x-service-info": acc_tk_service_info
            },
        )
        data = res.json()
        if data['code'] != '0001':
            break
        
        if progress_callback:
            progress_callback("인증 대기 중...")
            
        time.sleep(1)
    
    res = session.post(
        url=f'https://nice.checkplus.co.kr/cert/mobileCert/{method}/confirm/proc',
        headers={
            "X-Requested-With": "XMLHTTPRequest",
            "x-service-info": acc_tk_service_info
        },
    )
    data = res.text
    return data

def initialize_session(cp_data_url, isp):
    session = requests.Session()

    response = session.post(
        cp_data_url,
        json={"type": None, "childName": None, "childPhone": None}
    )
    data = response.json()
    m = 'checkplusService'
    encode_data = data['resMsg']
    wc_cookie = f'{uuid.uuid4()}_T_{random.randint(10000, 99999)}_WC'
    session.cookies.update({'wcCookie': wc_cookie})

    response = session.post('https://nice.checkplus.co.kr/CheckPlusSafeModel/checkplus.cb',
        data = {'m': m, 'EncodeData': encode_data}
    )
    data = response.text
    acc_tk_service_info = re.search(r'const\s+SERVICE_INFO\s*=\s*"([^"]+)"', data).group(1)

    session.post('https://nice.checkplus.co.kr/cert/main/menu',
        data = {"accTkInfo": acc_tk_service_info}
    )

    session.post('https://nice.checkplus.co.kr/cert/mobileCert/main',
        data = {"accTkInfo": acc_tk_service_info}
    )

    response = session.post(
        url='https://nice.checkplus.co.kr/cert/mobileCert/method',
        data = {
            "accTkInfo": acc_tk_service_info,
            "selectMobileCo": isp,
            "os": "Windows"
        }
    )

    data = response.text

    soup = BeautifulSoup(data, 'html.parser')
    cert_info_hash = soup.find('input', {'name': 'certInfoHash'})['value']

    return session, cert_info_hash, acc_tk_service_info


def verification(session, acc_tk_service_info):
    url = 'https://nice.checkplus.co.kr/cert/result/send'
    response = session.post(url,
        data = {
            "accTkInfo": acc_tk_service_info,
        }
    )
    
    data = response.text

    send_url_match = re.search(r'let\s+SEND_URL\s*=\s*"([^"]+)"', data)
    if send_url_match is None:
        sys.exit(1)
    send_url = send_url_match.group(1)

    query_string_match = re.search(r'const\s+queryString\s*=\s*"([^"]+)"', data)
    if query_string_match is None:
        sys.exit(1)
    query_string = query_string_match.group(1)
    
    url = f'{send_url}?{query_string}'
    response = session.post(url)
    auth_data = response.text # 사이트 마다 다르며 그냥 인증만 처리하거나 ci,di 등 부가 정보를 주기도 함

    return auth_data