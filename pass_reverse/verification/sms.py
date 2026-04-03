import re
from urllib.parse import quote
from pass_reverse.verification.utils.core import process_captcha_authentication, initialize_session, DEFAULT_CP_DATA_URL


def submit_sms_certification(session, acc_tk_service_info, name, birthdate, jumin, phone, captcha_answer):
    response = session.post(
        url='https://nice.checkplus.co.kr/cert/mobileCert/sms/certification/proc',
        headers={ 
            "X-Requested-With": "XMLHTTPRequest",
            "x-service-info": acc_tk_service_info
        },
        data={
            "userNameEncoding": quote(name),
            "userName": name,
            "myNum1": birthdate,
            "myNum2": jumin,
            "mobileNo": phone,
            "captchaAnswer": captcha_answer
        }
    )
    return response.json()


def sms_authentication_with_retry(session, cert_info_hash, acc_tk_service_info, name, birthdate, jumin, phone, 
                                  captcha_mode='auto', max_retries=3, captcha_input_callback=None, 
                                  sms_code_callback=None):
    cert_data = {"accTkInfo": acc_tk_service_info, "certInfoHash": cert_info_hash, "mobileCertAgree": "Y"}
    response_text = session.post('https://nice.checkplus.co.kr/cert/mobileCert/sms/certification', data=cert_data).text

    for attempt in range(1, max_retries + 1):
        captcha_answer = process_captcha_authentication(session, response_text, captcha_mode, captcha_input_callback)
        if not captcha_answer:
            raise ValueError("캡차 처리 실패")

        data = submit_sms_certification(session, acc_tk_service_info, name, birthdate, jumin, phone, captcha_answer)
        code = data.get('code', '')
        
        if code == 'SUCCESS':
            break
        
        error_msg = re.sub(r'<br\s*/?>', '\n', data.get('message', '')) if 'message' in data else None
        
        if code == 'RETRY':
            if attempt < max_retries:
                response_text = session.post('https://nice.checkplus.co.kr/cert/mobileCert/sms/certification', data=cert_data).text
                continue
            raise ValueError(f"최대 재시도 횟수를 초과했습니다. {error_msg or ''}")
        
        if code == 'FAIL':
            raise ValueError(f"인증 실패: {error_msg or ''}")

    session.post('https://nice.checkplus.co.kr/cert/mobileCert/sms/confirm')
    
    if not sms_code_callback:
        raise ValueError("SMS 인증코드 입력 콜백 함수가 필요합니다.")
    
    sms_code = sms_code_callback("SMS 인증코드를 입력하세요")
    session.post(
        'https://nice.checkplus.co.kr/cert/mobileCert/sms/confirm/proc',
        headers={"X-Requested-With": "XMLHTTPRequest", "x-service-info": acc_tk_service_info},
        data={"certCode": sms_code}
    )
    
    return session


def sms_authentication(isp, name, birthdate, jumin, phone, captcha_mode='auto', cp_data_url=None,
                      captcha_input_callback=None, sms_code_callback=None, max_retries=3):
    if not captcha_input_callback or not sms_code_callback:
        return False
    
    try:
        session, cert_info_hash, acc_tk_service_info = initialize_session(cp_data_url or DEFAULT_CP_DATA_URL, isp)
        sms_authentication_with_retry(
            session=session,
            cert_info_hash=cert_info_hash,
            acc_tk_service_info=acc_tk_service_info,
            name=name,
            birthdate=birthdate,
            jumin=jumin,
            phone=phone,
            captcha_mode=captcha_mode,
            max_retries=max_retries,
            captcha_input_callback=captcha_input_callback,
            sms_code_callback=sms_code_callback
        )
        return True
    except Exception:
        return False
