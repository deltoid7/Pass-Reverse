import re

def reg_exp(obj, type):
    ret = False
    try:
        reg_exp_pattern = ""
        if type == 'NAME':  # 이름
            reg_exp_pattern = r'\d'
            rs = re.findall(reg_exp_pattern, str(obj))
            ret = rs is None or len(rs) < 3
        else:
            if type == 'MYNUM1':  # 주민번호 앞자리
                reg_exp_pattern = r'^\d{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])$'
            elif type == 'MYNUM2':  # 주민번호 7번째 자리
                reg_exp_pattern = r'^\d{1}$'
            elif type == 'MOBILENO':  # 휴대폰번호
                reg_exp_pattern = r'^(\d{3})(\d{3,4})(\d{4})$'
            elif type == 'AUTHNUM':  # 인증 번호
                reg_exp_pattern = r'^\d{6}$'
            else:
                ret = True
            
            if reg_exp_pattern:
                ret = bool(re.match(reg_exp_pattern, str(obj)))
    except Exception as e:
        print(e)
        ret = True

    return ret


def check_reg_exp_layer(obj, type, msg):
    ret = reg_exp(obj, type)
    return (ret, msg)