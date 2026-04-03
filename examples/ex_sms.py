from pass_reverse.verification import sms_authentication
from pass_reverse.verification.utils.core import save_captcha_image


def captcha_callback(captcha_content, message):
    save_captcha_image(captcha_content, 'captcha.png')
    return input("캡차 답 입력: ")

def sms_code_callback(message):
    return input("SMS 인증코드 입력: ")


if __name__ == "__main__":
    isp = "통신사" # SK, SM, KT, KM, LG, LM (뒤에 M이 알뜰폰)
    
    name = '이름'
    birthdate = "YYMMDD"
    jumin = "주민등록번호 뒷자리 1번쨰"
    phone = '전화번호'
    
    print("SMS 인증 시작")
    success = sms_authentication(
        isp=isp,
        name=name,
        birthdate=birthdate,
        jumin=jumin,
        phone=phone,
        captcha_mode='auto', # auto는 캡차 모델로, manual은 사용자가 직접 해결 (콜백함수 이용)
        captcha_input_callback=captcha_callback,
        sms_code_callback=sms_code_callback,
        max_retries=3
    )
    
    if success:
        print("SMS 인증 성공!")
    else:
        print("SMS 인증 실패")