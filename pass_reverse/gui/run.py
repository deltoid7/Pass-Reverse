import uuid
import base64
import sys
import json
import hashlib
from pathlib import Path
from urllib.parse import urlencode
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import timedelta
from bs4 import BeautifulSoup
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

try:
    from ..verification.utils.core import initialize_session, extract_captcha_version, get_captcha_image, verification
    from ..verification.push import submit_push_certification
    from ..verification.sms import submit_sms_certification
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from pass_reverse.verification.utils.core import initialize_session, extract_captcha_version, get_captcha_image, verification
    from pass_reverse.verification.push import submit_push_certification
    from pass_reverse.verification.sms import submit_sms_certification

app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)


@app.context_processor
def inject_script_root():
    return {'script_root': request.script_root}

sessions_store = {}

DEFAULT_CP_DATA_URL = 'https://knvd.krcert.or.kr/api/core/pu/common/nice/get'
NICE_BASE_URL = 'https://nice.checkplus.co.kr'


def get_store():
    uid = session.get('uid')
    return sessions_store.get(uid)


def get_captcha_base64(req_session, captcha_version):
    if not captcha_version:
        return ""
    content = get_captcha_image(req_session, captcha_version)
    return base64.b64encode(content).decode('utf-8')


def build_cert_data(acc_tk_info, cert_info_hash):
    return {"accTkInfo": acc_tk_info, "certInfoHash": cert_info_hash, "mobileCertAgree": "Y"}


def build_ajax_headers(service_info):
    return {"X-Requested-With": "XMLHTTPRequest", "x-service-info": service_info}


def _get_aes_key(secret_key):
    return hashlib.sha256(secret_key.encode()).digest()


def encrypt_user_data(user_info, secret_key):
    key = _get_aes_key(secret_key)
    iv = os.urandom(16)
    
    data = json.dumps(user_info, ensure_ascii=False).encode('utf-8')
    pad_len = 16 - (len(data) % 16)
    data += bytes([pad_len] * pad_len)
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(data) + encryptor.finalize()
    
    return base64.urlsafe_b64encode(iv + encrypted).decode('utf-8')


def decrypt_user_data(encrypted_token, secret_key):
    key = _get_aes_key(secret_key)
    raw = base64.urlsafe_b64decode(encrypted_token)
    
    iv = raw[:16]
    encrypted = raw[16:]
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    
    pad_len = decrypted[-1]
    decrypted = decrypted[:-pad_len]
    
    return json.loads(decrypted.decode('utf-8'))


def get_success_response(store):
    user_info = {
        'isp': store.get('isp_name'),
        'isp_code': store.get('isp_code'),
        'cert_method': store.get('cert_method'),
        'user_name': store.get('user_name'),
        'mobile_no': store.get('mobile_no'),
        'birth_date': store.get('my_num1'),
    }
    
    redirect_url = app.config.get('PASS_SUCCESS_REDIRECT')
    if redirect_url:
        secret_key = app.secret_key
        encrypted_token = encrypt_user_data(user_info, secret_key)
        redirect_url = f"{redirect_url}?token={encrypted_token}"
        return {'code': 'SUCCESS', 'move_page': redirect_url}
    
    return {'code': 'SUCCESS', 'move_page': url_for('success')}


def init_cert_session(isp_code, cert_method):
    cp_data_url = app.config.get('CP_DATA_URL', DEFAULT_CP_DATA_URL)
    req_session, cert_info_hash, acc_tk_info = initialize_session(cp_data_url, isp_code)
    uid = session.get('uid')
    sessions_store[uid] = {
        'session': req_session,
        'acc_tk_info': acc_tk_info,
        'cert_info_hash': cert_info_hash,
        'isp_name': session.get('isp_name'),
        'isp_code': isp_code,
        'cert_method': cert_method
    }
    return req_session, cert_info_hash, acc_tk_info


def extract_qr_data(req_session, acc_tk_info, cert_info_hash):
    cert_data = build_cert_data(acc_tk_info, cert_info_hash)
    qr_page_res = req_session.post(f'{NICE_BASE_URL}/cert/mobileCert/qr/certification', data=cert_data)
    
    qr_num_element = BeautifulSoup(qr_page_res.text, 'html.parser').find('div', class_='qr_num')
    if not qr_num_element:
        return None, None
    
    qr_num = qr_num_element.text.strip()
    qr_image_content = req_session.post(f'{NICE_BASE_URL}/cert/qr/image/{qr_num}').content
    qr_image_base64 = base64.b64encode(qr_image_content).decode('utf-8')
    
    return qr_num, qr_image_base64


@app.before_request
def make_session_permanent():
    session.permanent = True
    if 'uid' not in session:
        session['uid'] = str(uuid.uuid4())


@app.route('/')
def index():
    uid = session.get('uid')
    if uid in sessions_store:
        del sessions_store[uid]
    session.clear()
    session['uid'] = str(uuid.uuid4())
    return redirect(url_for('select_isp'))


@app.route('/select_isp', methods=['GET'])
def select_isp():
    return render_template('select_isp.html')


@app.route('/select_method', methods=['GET', 'POST'])
def select_method():
    if request.method == 'POST':
        isp_name = request.form.get('selectMobileCo')
        isp_code = request.form.get('ispCode')
        if isp_name:
            session['isp_name'] = isp_name
            session['isp_code'] = isp_code
            return render_template('select_method.html', isp_name=isp_name)
    
    isp_name = session.get('isp_name')
    if not isp_name:
        return redirect(url_for('select_isp'))
    return render_template('select_method.html', isp_name=isp_name)


@app.route('/push', methods=['GET', 'POST'])
def push():
    isp_name = session.get('isp_name')
    isp_code = session.get('isp_code')
    if not isp_name or not isp_code:
        return redirect(url_for('select_isp'))
    
    req_session, cert_info_hash, acc_tk_info = init_cert_session(isp_code, 'PUSH')
    
    cert_data = build_cert_data(acc_tk_info, cert_info_hash)
    push_page_res = req_session.post(f'{NICE_BASE_URL}/cert/mobileCert/push/certification', data=cert_data)
    
    captcha_version = extract_captcha_version(push_page_res.text)
    captcha_base64 = get_captcha_base64(req_session, captcha_version)
    
    return render_template('methods/push/push.html',
                           captchaVersion=captcha_version,
                           captchaBase64=captcha_base64,
                           isp_name=isp_name)


@app.route('/refresh_captcha', methods=['POST'])
def refresh_captcha():
    store = get_store()
    if not store:
        return jsonify({'code': 'FAIL', 'message': 'Session expired'})
    
    req_session = store['session']
    cert_data = build_cert_data(store['acc_tk_info'], store['cert_info_hash'])
    push_page_res = req_session.post(f'{NICE_BASE_URL}/cert/mobileCert/push/certification', data=cert_data)
    
    captcha_version = extract_captcha_version(push_page_res.text)
    captcha_base64 = get_captcha_base64(req_session, captcha_version)
    
    return jsonify({'code': 'SUCCESS', 'captchaVersion': captcha_version, 'captchaBase64': captcha_base64})


@app.route('/submit_push', methods=['POST'])
def submit_push():
    store = get_store()
    if not store:
        return redirect(url_for('select_isp'))
    
    user_name = request.form.get('userName')
    mobile_no = request.form.get('mobileNo')
    captcha_answer = request.form.get('captchaAnswer')
    
    store['user_name'] = user_name
    store['mobile_no'] = mobile_no
    store['captcha_answer'] = captcha_answer
    
    result = submit_push_certification(store['session'], store['acc_tk_info'], user_name, mobile_no, captcha_answer)
    
    if result.get('code') == 'SUCCESS':
        return jsonify({'code': 'SUCCESS', 'redirect': url_for('push_confirm')})
    return jsonify({'code': 'FAIL', 'message': result.get('message', '인증 실패')})


@app.route('/push_confirm')
def push_confirm():
    store = get_store()
    if not store:
        return redirect(url_for('select_isp'))
    return render_template('methods/push/push_confirm.html', isp_name=store.get('isp_name'))


@app.route('/push/confirm/proc', methods=['POST'])
def push_confirm_proc():
    store = get_store()
    if not store:
        return jsonify({'code': 'FAIL', 'message': 'Session expired'})
    
    session_obj = store['session']
    service_info = store['acc_tk_info']
    headers = build_ajax_headers(service_info)
    
    status_res = session_obj.post(f'{NICE_BASE_URL}/cert/polling/confirm/check/proc', headers=headers)
    
    if status_res.json().get('code') == '0001':
        return jsonify({'code': 'RETRY'})
    
    session_obj.post(f'{NICE_BASE_URL}/cert/mobileCert/push/confirm/proc', headers=headers)
    
    verification(session_obj, service_info)
    
    return jsonify(get_success_response(store))


@app.route('/sms', methods=['GET', 'POST'])
def sms():
    isp_name = session.get('isp_name')
    isp_code = session.get('isp_code')
    if not isp_name or not isp_code:
        return redirect(url_for('select_isp'))
    
    req_session, cert_info_hash, acc_tk_info = init_cert_session(isp_code, 'SMS')
    
    cert_data = build_cert_data(acc_tk_info, cert_info_hash)
    sms_page_res = req_session.post(f'{NICE_BASE_URL}/cert/mobileCert/sms/certification', data=cert_data)
    
    captcha_version = extract_captcha_version(sms_page_res.text)
    captcha_base64 = get_captcha_base64(req_session, captcha_version)
    
    return render_template('methods/sms/sms.html',
                           captchaVersion=captcha_version,
                           captchaBase64=captcha_base64,
                           isp_name=isp_name)


@app.route('/refresh_captcha_sms', methods=['POST'])
def refresh_captcha_sms():
    store = get_store()
    if not store:
        return jsonify({'code': 'FAIL', 'message': 'Session expired'})
    
    req_session = store['session']
    cert_data = build_cert_data(store['acc_tk_info'], store['cert_info_hash'])
    sms_page_res = req_session.post(f'{NICE_BASE_URL}/cert/mobileCert/sms/certification', data=cert_data)
    
    captcha_version = extract_captcha_version(sms_page_res.text)
    captcha_base64 = get_captcha_base64(req_session, captcha_version)
    
    return jsonify({'code': 'SUCCESS', 'captchaVersion': captcha_version, 'captchaBase64': captcha_base64})


@app.route('/submit_sms', methods=['POST'])
def submit_sms():
    store = get_store()
    if not store:
        return jsonify({'code': 'FAIL', 'message': 'Session expired'})
    
    user_name = request.form.get('userName')
    mobile_no = request.form.get('mobileNo')
    my_num1 = request.form.get('myNum1')
    my_num2 = request.form.get('myNum2')
    captcha_answer = request.form.get('captchaAnswer')
    
    store['user_name'] = user_name
    store['mobile_no'] = mobile_no
    store['my_num1'] = my_num1
    store['my_num2'] = my_num2
    store['captcha_answer'] = captcha_answer
    
    result = submit_sms_certification(store['session'], store['acc_tk_info'], user_name, my_num1, my_num2, mobile_no, captcha_answer)
    
    if result.get('code') == 'SUCCESS':
        store['session'].post(f'{NICE_BASE_URL}/cert/mobileCert/sms/confirm')
        return jsonify({'code': 'SUCCESS', 'redirect': url_for('sms_confirm')})
    return jsonify({'code': 'FAIL', 'message': result.get('message', '인증 실패')})


@app.route('/sms_confirm')
def sms_confirm():
    store = get_store()
    if not store:
        return redirect(url_for('select_isp'))
    return render_template('methods/sms/sms_confirm.html', isp_name=store.get('isp_name'))


@app.route('/sms/confirm/proc', methods=['POST'])
def sms_confirm_proc():
    store = get_store()
    if not store:
        return jsonify({'code': 'FAIL', 'message': 'Session expired'})
    
    cert_code = request.form.get('certCode')
    headers = build_ajax_headers(store['acc_tk_info'])
    
    result = store['session'].post(
        f'{NICE_BASE_URL}/cert/mobileCert/sms/confirm/proc',
        headers=headers,
        data={"certCode": cert_code}
    )
    
    data = result.json()
    code = data.get('code')
    
    if code == 'SUCCESS':
        verification(store['session'], store['acc_tk_info'])
        response = get_success_response(store)
        response['message'] = data.get('message', '')
        return jsonify(response)
    if code == 'RETRY':
        return jsonify({'code': 'RETRY', 'message': data.get('message', ''), 'sub_message': data.get('subMessage', '')})
    return jsonify({'code': 'FAIL', 'message': data.get('message', '인증에 실패했습니다.')})


@app.route('/sms/resend/proc', methods=['POST'])
def sms_resend_proc():
    store = get_store()
    if not store:
        return jsonify({'code': 'FAIL', 'message': 'Session expired'})
    
    req_session = store['session']
    cert_data = build_cert_data(store['acc_tk_info'], store['cert_info_hash'])
    req_session.post(f'{NICE_BASE_URL}/cert/mobileCert/sms/certification', data=cert_data)
    
    result = submit_sms_certification(
        req_session,
        store['acc_tk_info'],
        store.get('user_name'),
        store.get('my_num1'),
        store.get('my_num2'),
        store.get('mobile_no'),
        store.get('captcha_answer')
    )
    
    if result.get('code') == 'SUCCESS':
        req_session.post(f'{NICE_BASE_URL}/cert/mobileCert/sms/confirm')
        return jsonify({'code': 'SUCCESS', 'message': '인증번호가 재발송되었습니다.'})
    return jsonify({'code': 'FAIL', 'message': result.get('message', '재발송에 실패했습니다.')})


@app.route('/qr', methods=['GET', 'POST'])
def qr():
    isp_name = session.get('isp_name')
    isp_code = session.get('isp_code')
    if not isp_name or not isp_code:
        return redirect(url_for('select_isp'))
    
    req_session, cert_info_hash, acc_tk_info = init_cert_session(isp_code, 'QR')
    
    qr_num, qr_image_base64 = extract_qr_data(req_session, acc_tk_info, cert_info_hash)
    if not qr_num:
        return redirect(url_for('error'))

    uid = session.get('uid')
    sessions_store[uid]['qr_num'] = qr_num
    
    return render_template('methods/qr/qr.html',
                           qr_num=qr_num,
                           qr_image_base64=qr_image_base64,
                           isp_name=isp_name)


@app.route('/qr/confirm/proc', methods=['POST'])
def qr_confirm_proc():
    store = get_store()
    if not store:
        return jsonify({'code': 'FAIL', 'message': 'Session expired'})
    
    session_obj = store['session']
    service_info = store['acc_tk_info']
    headers = build_ajax_headers(service_info)
    
    status_res = session_obj.post(f'{NICE_BASE_URL}/cert/polling/confirm/check/proc', headers=headers)
    
    if status_res.json().get('code') == '0001':
        return jsonify({'code': 'RETRY'})
    
    session_obj.post(f'{NICE_BASE_URL}/cert/mobileCert/qr/confirm/proc', headers=headers)
    
    verification(session_obj, service_info)
    
    return jsonify(get_success_response(store))


@app.route('/qr/extend', methods=['POST'])
def qr_extend():
    store = get_store()
    if not store:
        return jsonify({'code': 'FAIL', 'message': 'Session expired'})
    
    qr_num, qr_image_base64 = extract_qr_data(store['session'], store['acc_tk_info'], store['cert_info_hash'])
    if not qr_num:
        return jsonify({'code': 'FAIL', 'message': 'QR 번호를 가져올 수 없습니다.'})
    
    uid = session.get('uid')
    sessions_store[uid]['qr_num'] = qr_num
    
    return jsonify({'code': 'SUCCESS', 'qr_num': qr_num, 'qr_image_base64': qr_image_base64})


@app.route('/success')
def success():
    store = get_store()
    if not store:
        return redirect(url_for('select_isp'))

    birth_date = store.get('my_num1', None)
    
    return render_template('success.html',
                           isp=store.get('isp_name'),
                           isp_code=store.get('isp_code'),
                           cert_method=store.get('cert_method'),
                           user_name=store.get('user_name'),
                           mobile_no=store.get('mobile_no'),
                           birth_date=birth_date,
                           captcha_answer=store.get('captcha_answer'))


@app.route('/error')
def error():
    return render_template('error.html')


def run_app(host='0.0.0.0', port=5000, debug=False, success_redirect=None, 
            secret_key='secret', cp_data_url=None):
    app.secret_key = secret_key
    app.config['PASS_SUCCESS_REDIRECT'] = success_redirect
    if cp_data_url:
        app.config['CP_DATA_URL'] = cp_data_url
    app.run(debug=debug, host=host, port=port)


if __name__ == '__main__':
    run_app()
