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
from pass_reverse.verification.utils.core import verification

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


def wait_for_confirm(session, acc_tk_service_info, method):
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

    response = session.get(cp_data_url)
    data = response.text

    m = re.search(r'name=["\']m["\']\s+value=["\']([^"\']+)["\']', data).group(1)
    encode_data = re.search(r'name=["\']EncodeData["\']\s+value=["\']([^"\']+)["\']', data).group(1)
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


def sms_authentication(session, cert_info_hash, acc_tk_service_info, name, birthdate, jumin, phone, captcha_mode='manual'):
    response = session.post(
        url='https://nice.checkplus.co.kr/cert/mobileCert/sms/certification',
        data = {
            "accTkInfo": acc_tk_service_info,
            "certInfoHash": cert_info_hash,
            "mobileCertAgree": "Y"
        }
    )

    data = response.text
    captcha_version = re.search(r'const\s+captchaVersion\s*=\s*"([^"]+)"', data).group(1)

    response = session.get(f'https://nice.checkplus.co.kr/cert/captcha/image/{captcha_version}')
    captcha_content = response.content

    if captcha_mode == "auto":
        result = solve_captcha(captcha_content)
        if result == "FAILED":
            with open('captcha.png', 'wb') as f:
                f.write(captcha_content)
            captcha_answer = input("[자동 인증 실패] Captcha 답을 입력하세요: ")
        else:
            captcha_answer = result
    else:
        with open('captcha.png', 'wb') as f:
            f.write(captcha_content)
        captcha_answer = input("Captcha 답을 입력하세요: ")

    response = session.post(
        url='https://nice.checkplus.co.kr/cert/mobileCert/sms/certification/proc',
        headers={ 
            "X-Requested-With": "XMLHTTPRequest",
            "x-service-info": acc_tk_service_info
        },
        data = {
            "userNameEncoding": quote(name),
            "userName": name,
            "myNum1": birthdate,
            "myNum2": jumin,
            "mobileNo": phone,
            "captchaAnswer": captcha_answer
        }
    )

    data = response.json()
    code = data['code']

    if code != 'SUCCESS':
        msg = re.sub(r'<br\s*/?>', '\n', data['message'])
        print(msg)

    if code == 'RETRY':
        print('다시 시도') # 다시 시도 로직 넣기
        pass

    if code == 'FAIL':
        print('실패') # 실패 시 로직 넣기
        pass

    response = session.post('https://nice.checkplus.co.kr/cert/mobileCert/sms/confirm')
    data = response.text

    sms_code = input("SMS 인증코드를 입력하세요: ")

    response = session.post(
        url='https://nice.checkplus.co.kr/cert/mobileCert/sms/confirm/proc',
        headers={
            "X-Requested-With": "XMLHTTPRequest",
            "x-service-info": acc_tk_service_info
        },
        data = {
            "certCode": sms_code
        }
    )
    data = response.text
    return session


def push_authentication(session, cert_info_hash, acc_tk_service_info, name, phone, captcha_mode='manual'):
    response = session.post(
        url='https://nice.checkplus.co.kr/cert/mobileCert/push/certification',
        data = {
            "accTkInfo": acc_tk_service_info,
            "certInfoHash": cert_info_hash,
            "mobileCertAgree": "Y"
        }
    )

    data = response.text
    captcha_version = re.search(r'const\s+captchaVersion\s*=\s*"([^"]+)"', data).group(1)

    captcha_request = session.get(f'https://nice.checkplus.co.kr/cert/captcha/image/{captcha_version}')
    captcha_content = captcha_request.content

    if captcha_mode == "auto":
        result = solve_captcha(captcha_content)
        if result == "FAILED":
            with open('captcha.png', 'wb') as f:
                f.write(captcha_content)
            captcha_answer = input("[자동 인증 실패] Captcha 답을 입력하세요: ")
        else:
            captcha_answer = result
    else:
        with open('captcha.png', 'wb') as f:
            f.write(captcha_content)
        captcha_answer = input("Captcha 답을 입력하세요: ")

    response = session.post(
        url='https://nice.checkplus.co.kr/cert/mobileCert/push/certification/proc',
        headers={
            "X-Requested-With": "XMLHTTPRequest",
            "x-service-info": acc_tk_service_info
        },
        data = {
            "userNameEncoding": quote(name),
            "userName": name,
            "mobileNo": phone,
            "captchaAnswer": captcha_answer
        }
    )
    
    print("PASS 앱 알림 확인하고 인증을 진행해주세요.")
    data = wait_for_confirm(session, acc_tk_service_info, "push")
    return session


def qr_authentication(session, cert_info_hash, acc_tk_service_info):
    response = session.post(
        url='https://nice.checkplus.co.kr/cert/mobileCert/qr/certification',
        data = {
            "accTkInfo": acc_tk_service_info,
            "certInfoHash": cert_info_hash,
            "mobileCertAgree": "Y"
        }
    )

    data = response.text

    qr_soup = BeautifulSoup(data, 'html.parser')
    qr_num_element = qr_soup.find('div', class_='qr_num')
    qr_num = qr_num_element.text.strip() if qr_num_element else None

    qr_image_res = session.post(url=f'https://nice.checkplus.co.kr/cert/qr/image/{qr_num}')
    qr_image = qr_image_res.content

    with open('qr.png', 'wb') as f:
        f.write(qr_image)

    print(f"PASS앱 실행 후, 상단의 QR인증에서 QR코드 스캔 또는 인증번호 입력을 선택해주세요. (인증번호: {qr_num})")
    data = wait_for_confirm(session, acc_tk_service_info, "qr")
    return session


if __name__ == "__main__":
    isp = "통신사" # SK, SM, KT, KM, LG, LM (뒤에 M이 알뜰폰)
    method = "인증방식" # sms, qr, push

    cp_data_url = 'https://knvd.krcert.or.kr/reportNonMemberAuth.do'
    # cp_data_url = 'https://www.ex.co.kr:8070/recruit/company/nice/checkplus_main_company.jsp' # 해당 주소로 인증하면 ci,di 예시를 받을 수 있습니다.
    session, cert_info_hash, acc_tk_service_info = initialize_session(cp_data_url, isp)

    if method == "qr":
        auth_session = qr_authentication(session, cert_info_hash, acc_tk_service_info)
    else:
        name = "이름"
        birthdate = "YYMMDD"
        jumin = "주민등록번호 뒷자리 1번쨰"
        phone = "전화번호"
        validate_inputs(name, birthdate, jumin, phone)

        captcha_mode = "캡차 인증 방식" # auto면 캡차 모델 이용해서 자동 해결, manual이면 사용자가 직접 해결 / 자세한 사용은 examples 폴더 참조 (콜백 구현)

        if method == "sms":
            auth_session = sms_authentication(session, cert_info_hash, acc_tk_service_info, name, birthdate, jumin, phone, captcha_mode)
        elif method == "push":
            auth_session = push_authentication(session, cert_info_hash, acc_tk_service_info, name, phone, captcha_mode)
        else:
            print("올바르지 않은 인증방식")

        data = verification(auth_session, acc_tk_service_info)
        if '오류' in data:
            print("실패")
        else:
            print("성공")