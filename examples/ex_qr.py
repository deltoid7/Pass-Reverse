from pass_reverse.verification import qr_authentication
from pass_reverse.verification.utils import core


def progress_callback(message):
    print(message)

def wait_for_confirm_with_progress(session, acc_tk_service_info, method):
    return core.wait_for_confirm(
        session=session,
        acc_tk_service_info=acc_tk_service_info,
        method=method,
        progress_callback=progress_callback
    )


if __name__ == "__main__":
    isp = "통신사" # SK, SM, KT, KM, LG, LM (뒤에 M이 알뜰폰)
    
    print("QR 인증 시작")
    success = qr_authentication(
        isp=isp,
        wait_for_confirm_func=wait_for_confirm_with_progress 
    )
    
    if success:
        print("QR 인증 성공!")
    else:
        print("QR 인증 실패")
