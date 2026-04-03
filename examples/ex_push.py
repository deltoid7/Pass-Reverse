from pass_reverse.verification import push_authentication
from pass_reverse.verification.utils.core import save_captcha_image, wait_for_confirm


def captcha_callback(captcha_content, message):
    save_captcha_image(captcha_content, 'captcha.png')
    return input("캡차 답 입력: ")

def progress_callback(message):
    print(message)

def wait_for_confirm_with_progress(session, acc_tk_service_info, method):
    return wait_for_confirm(
        session=session,
        acc_tk_service_info=acc_tk_service_info,
        method=method,
        progress_callback=progress_callback
    )


if __name__ == "__main__":
    isp = "통신사" # SK, SM, KT, KM, LG, LM (뒤에 M이 알뜰폰)
    
    name = '이름'
    phone = '전화번호'

    print("Push 인증 시작")
    success = push_authentication(
        isp=isp,
        name=name,
        phone=phone,
        captcha_mode='auto', # auto는 캡차 모델로, manual은 사용자가 직접 해결 (콜백함수 이용)
        captcha_input_callback=captcha_callback,
        wait_for_confirm_func=wait_for_confirm_with_progress,
        max_retries=3
    )
    
    if success:
        print("Push 인증 성공!")
    else:
        print("Push 인증 실패")
