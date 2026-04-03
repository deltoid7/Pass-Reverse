import re
from urllib.parse import quote
from pass_reverse.verification.utils.core import process_captcha_authentication, initialize_session, wait_for_confirm, DEFAULT_CP_DATA_URL


def submit_push_certification(session, acc_tk_service_info, name, phone, captcha_answer):
    response = session.post(
        url='https://nice.checkplus.co.kr/cert/mobileCert/push/certification/proc',
        headers={
            "X-Requested-With": "XMLHTTPRequest",
            "x-service-info": acc_tk_service_info
        },
        data={
            "userNameEncoding": quote(name),
            "userName": name,
            "mobileNo": phone,
            "captchaAnswer": captcha_answer
        }
    )
    return response.json()


def push_authentication_with_retry(session, cert_info_hash, acc_tk_service_info, name, phone, 
                                   captcha_mode='auto', max_retries=3, wait_for_confirm_func=None, 
                                   captcha_input_callback=None):
    cert_data = {"accTkInfo": acc_tk_service_info, "certInfoHash": cert_info_hash, "mobileCertAgree": "Y"}
    response_text = session.post('https://nice.checkplus.co.kr/cert/mobileCert/push/certification', data=cert_data).text

    for attempt in range(1, max_retries + 1):
        captcha_answer = process_captcha_authentication(session, response_text, captcha_mode, captcha_input_callback)
        if not captcha_answer:
            raise ValueError("캡차 처리 실패")

        data = submit_push_certification(session, acc_tk_service_info, name, phone, captcha_answer)
        code = data.get('code', '')
        
        if code == 'SUCCESS':
            break
        
        error_msg = re.sub(r'<br\s*/?>', '\n', data.get('message', '')) if 'message' in data else None
        
        if code == 'RETRY':
            if attempt < max_retries:
                response_text = session.post('https://nice.checkplus.co.kr/cert/mobileCert/push/certification', data=cert_data).text
                continue
            raise ValueError(f"최대 재시도 횟수를 초과했습니다. {error_msg or ''}")
        
        if code == 'FAIL':
            raise ValueError(f"인증 실패: {error_msg or ''}")

    if wait_for_confirm_func:
        wait_for_confirm_func(session, acc_tk_service_info, "push")
    
    return session


def push_authentication(isp, name, phone, captcha_mode='auto', cp_data_url=None,
                       captcha_input_callback=None, wait_for_confirm_func=None, max_retries=3):
    if not captcha_input_callback:
        return False
    
    try:
        session, cert_info_hash, acc_tk_service_info = initialize_session(cp_data_url or DEFAULT_CP_DATA_URL, isp)
        push_authentication_with_retry(
            session=session,
            cert_info_hash=cert_info_hash,
            acc_tk_service_info=acc_tk_service_info,
            name=name,
            phone=phone,
            captcha_mode=captcha_mode,
            max_retries=max_retries,
            wait_for_confirm_func=wait_for_confirm_func or wait_for_confirm,
            captcha_input_callback=captcha_input_callback
        )
        return True
    except Exception:
        return False
