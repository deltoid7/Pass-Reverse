from bs4 import BeautifulSoup
from pass_reverse.verification.utils.core import initialize_session, wait_for_confirm, DEFAULT_CP_DATA_URL


def qr_authentication_with_confirm(session, cert_info_hash, acc_tk_service_info, wait_for_confirm_func=None):
    response = session.post(
        'https://nice.checkplus.co.kr/cert/mobileCert/qr/certification',
        data={"accTkInfo": acc_tk_service_info, "certInfoHash": cert_info_hash, "mobileCertAgree": "Y"}
    )

    qr_num_element = BeautifulSoup(response.text, 'html.parser').find('div', class_='qr_num')
    if not qr_num_element:
        raise ValueError("QR 번호를 찾을 수 없습니다.")
    
    qr_num = qr_num_element.text.strip()
    qr_image = session.post(f'https://nice.checkplus.co.kr/cert/qr/image/{qr_num}').content

    if wait_for_confirm_func:
        wait_for_confirm_func(session, acc_tk_service_info, "qr")
    
    return session, {
        'qr_num': qr_num,
        'qr_image': qr_image,
        'message': f"PASS앱 실행 후, 상단의 QR인증에서 QR코드 스캔 또는 인증번호 입력을 선택해주세요. (인증번호: {qr_num})"
    }


def qr_authentication(isp, cp_data_url=None, wait_for_confirm_func=None):
    try:
        session, cert_info_hash, acc_tk_service_info = initialize_session(cp_data_url or DEFAULT_CP_DATA_URL, isp)
        qr_authentication_with_confirm(
            session=session,
            cert_info_hash=cert_info_hash,
            acc_tk_service_info=acc_tk_service_info,
            wait_for_confirm_func=wait_for_confirm_func or wait_for_confirm
        )
        return True
    except Exception:
        return False
