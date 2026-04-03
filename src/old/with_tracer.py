import requests
import re
import random
import uuid
from urllib.parse import quote
from urllib3.connectionpool import Url
from bs4 import BeautifulSoup
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pass_reverse.verification.utils.check_reg import check_reg_exp_layer
from pass_reverse.verification.utils.captcha_solver import solve_captcha

user_agent = 'mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 (khtml, like gecko) chrome/138.0.0.0 safari/537.36'

HOST_ISP_MAPPING = {
    "SK": "SKT",
    "SM": "SKT",
    "KT": "KT",
    "KM": "KT",
    "LG": "LGU",
    "LM": "LGU"
}


def validate_inputs(name, birthdate, jumin, phone):
    result1, msg1 = check_reg_exp_layer(name, "NAME", "올바른 이름을 입력해주세요.")
    result2, msg2 = check_reg_exp_layer(birthdate, "MYNUM1", "올바른 생년월일을 입력해주세요.")
    result3, msg3 = check_reg_exp_layer(jumin, "MYNUM2", "올바른 성별을 입력해주세요.")
    result4, msg4 = check_reg_exp_layer(phone, "MOBILENO", "올바른 휴대폰 번호를 입력해주세요.")

    errors = []
    if not result1:
        errors.append(msg1)
    if not result2:
        errors.append(msg2)
    if not result3:
        errors.append(msg3)
    if not result4:
        errors.append(msg4)

    if errors:
        msg = errors[0]
        print(msg)
        sys.exit(1)


def initialize_session(cp_data_url, isp):
    session = requests.Session()

    response = session.get(cp_data_url)
    data = response.text

    m = re.search(r'name=["\']m["\']\s+value=["\']([^"\']+)["\']', data).group(1)
    encode_data = re.search(r'name=["\']EncodeData["\']\s+value=["\']([^"\']+)["\']', data).group(1)
    wc_cookie = f'{uuid.uuid4()}_T_{random.randint(10000, 99999)}_WC'
    session.cookies.update({'wcCookie': wc_cookie})

    response = session.post('https://nice.checkplus.co.kr/CheckPlusSafeModel/checkplus.cb',
        data={'m': m, 'EncodeData': encode_data}
    )
    data = response.text
    acc_tk_service_info = re.search(r'const\s+SERVICE_INFO\s*=\s*"([^"]+)"', data).group(1)

    response = session.post('https://nice.checkplus.co.kr/cert/main/tracer',
        data={"accTkInfo": acc_tk_service_info}
    )
    data = response.text

    try:
        ip = re.search(r'callTracerApiInput\(\s*"[^"]*",\s*"(\d{1,3}(?:\.\d{1,3}){3})",', data).group(1)
    except:
        print('IP가 차단당했습니다.')
        sys.exit(1)

    session.post('https://ifc.niceid.co.kr/TRACERAPI/inputQueue.do',
        data={
            "host": 'COMMON_CHECKPLUS',
            "ip": ip,
            "loginId": wc_cookie,
            "port": "80",
            "pageUrl": "service",
            "userAgent": user_agent
        }
    )

    session.post('https://nice.checkplus.co.kr/cert/main/menu',
        data={"accTkInfo": acc_tk_service_info}
    )

    session.post('https://ifc.niceid.co.kr/TRACERAPI/inputQueue.do',
        data={
            "host": 'COMMON_MOBILE',
            "ip": ip,
            "loginId": wc_cookie,
            "port": "80",
            "pageUrl": "mobile_cert",
            "userAgent": user_agent
        }
    )

    session.post('https://nice.checkplus.co.kr/cert/mobileCert/main',
        data={"accTkInfo": acc_tk_service_info}
    )
    
    session.post('https://ifc.niceid.co.kr/TRACERAPI/inputQueue.do',
        data={
            "host": f'COMMON_MOBILE_{HOST_ISP_MAPPING.get(isp)}',
            "ip": ip,
            "loginId": wc_cookie,
            "port": "80",
            "pageUrl": "mobile_cert_telecom",
            "userAgent": user_agent
        }
    )

    response = session.post(
        url='https://nice.checkplus.co.kr/cert/mobileCert/method',
        data={
            "accTkInfo": acc_tk_service_info,
            "selectMobileCo": isp,
            "os": "Windows"
        }
    )

    data = response.text

    soup = BeautifulSoup(data, 'html.parser')
    cert_info_hash = soup.find('input', {'name': 'certInfoHash'})['value']

    return session, cert_info_hash, acc_tk_service_info