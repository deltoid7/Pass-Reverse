//
$(function () {

    //통신사 클릭 이벤트
    $('.tel_item').click(function(){
        $(this).attr('aria-selected','true').addClass("on").focus().siblings().removeClass("on").attr('aria-selected','false');
    });

    //통신사 선택 후 페이지 이동
    $('.mobileCoCheck').click(function(){
        const ispCode = $(this).val();
        const ispNameMap = {
            'SK': 'SKT',
            'KT': 'KT',
            'LG': 'LG U+',
            'SM': 'SKT 알뜰폰',
            'KM': 'KT 알뜰폰',
            'LM': 'LG U+ 알뜰폰'
        };
        const ispName = ispNameMap[ispCode] || ispCode;
        $('#selectMobileCo').val(ispName);
        $('#ispCode').val(ispCode);
        $('#frm').submit();
    });

    //알뜰폰 탭
    $(".saveTel_item:first-child .tab_txt").addClass('on').attr({ "tabindex": "0"});
    $(".saveTel_item:first-child").children('button').addClass('on').attr({"aria-selected":"true"});

    $(".saveTel_item button").click(function () {
        //tab 클릭
        $(".saveTel_item button").removeClass("on").attr({ "aria-selected": "false" });
        $(this).addClass("on").attr({ "aria-selected": "true" });
        //tab 본문
        $(".tab_txt").removeClass('on').attr('tabindex', -1);
        $("#" + $(this).attr("aria-controls")).addClass("on").attr('tabindex', 0);
    });

    //인증방법 목록 이벤트
    $(".cert_item").click(function () {
        // 현재 클릭된 항목
        const $clickedItem = $(this);

        // 현재 클릭된 항목에 'on' 클래스 추가 및 형제 요소에서 'on' 클래스 제거
        $clickedItem.addClass('on').siblings().removeClass('on');

        // 인증방법 값 설정
        const method = $clickedItem.find('.mobileCertMethodCheck').val();
        $('#certMethod').val(method);

        // 인증 내용 영역에서 'group_bottom' 클래스 추가
        $(".cert_content .group_bottom").addClass("on");

        // 모든 항목의 버튼 title 속성 설정
        $('.cert_item').each(function () {
            const $item = $(this);
            const itemTit = $item.find('.item_tit strong').text();
            const titleText = $item.is($clickedItem) ? itemTit + ' 선택됨' : itemTit + ' 선택 안됨';
            $item.find('button').attr('title', titleText);
        });
    });

    //약관동의 체크박스 이벤트
    $(".checkbox input").click(function () {
        $(this).toggleClass('checked');
    });

    // 인증방법 동의 체크박스, 버튼 활성화
    $('#mobileCertAgree').click(function() {
        if ($('#mobileCertAgree').hasClass("ui_non") === false) {
            if ($('#mobileCertAgree').hasClass('checked')) {
                $('.btn_pass').addClass('show');
            } else {
                $('.btn_pass').removeClass('show');
            }
        }
    });

    // 다음 버튼 클릭
    $('#btnMobileCertStart').click(function(){
        if ($(this).hasClass('show')) {
            const method = $('#certMethod').val();
            const urls = typeof PASS_URLS !== 'undefined' ? PASS_URLS : {
                push: '/push', sms: '/sms', qr: '/qr', error: '/error'
            };
            if (method === 'APP_PUSH') {
                $('#frm').attr('action', urls.push);
            } else if (method === 'SMS') {
                $('#frm').attr('action', urls.sms);
            } else if (method === 'APP_QR') {
                $('#frm').attr('action', urls.qr);
            } else {
                $('#frm').attr('action', urls.error);
            }
            $('#frm').submit();
        }
    });

    // SMS 성명 확인 후 다음 단계
    $('.certWay_content.sms .btnUserName').one("click", function(){
        if ($(this).hasClass("btnUserName")) {
            $('#infoBirth').addClass('on').siblings().removeClass('on');
            $('.step_id').addClass('on');
            $('.btnUserName').removeClass('show').removeClass('btnUserName').addClass('btnSubmit');
            $('#myNum1').focus();
        }
    })

    // PASS 성명 확인 후 다음 단계
    $('.certWay_content.pass .btnUserName').one("click", function(){
        if ($(this).hasClass("btnUserName")) {
            $('#infoTel').addClass('on').siblings().removeClass('on');
            $('.step_tel').addClass('on');
            $('.btnUserName').removeClass('show').removeClass('btnUserName').addClass('btnSubmit');
            $('#mobileNo').focus();
        }
    })

    $('#myNum1').on('keydown', function (e) {
        if (e.keyCode !== 8 && e.keyCode !== 16 && e.keyCode !== 9) {
            // number 타입에 대한 길이 값 조정
            if ($(this).attr("type")  === 'number' && $(this).val().length === 6) {
                return false;
            }
        }
    });

    $('#myNum2').on('keydown', function (e) {
        if (e.keyCode !== 8 && e.keyCode !== 16 && e.keyCode !== 9) {
            // number 타입에 대한 길이 값 조정
            if ($(this).attr("type") === 'number' && $(this).val().length === 1) {
                return false;
            }
        }
    });

    $('#mobileNo').on('keydown', function (e) {
        if (e.keyCode !== 8 && e.keyCode !== 16 && e.keyCode !== 9) {
            // number 타입에 대한 길이 값 조정
            if ($(this).attr("type") === 'number' && $(this).val().length === 11) {
                return false;
            }
        }
    });

    // 성명에 대한 처리
    $('#userName').on('keyup', function () {
        if ($('#userName').val().length > 0) {
            $('.btnUserName').addClass('show');
        } else if($('#userName').val().length < 1) {
            $('.btnUserName').removeClass('show');
            // 이름이 지워지면 다시 이름 입력 타이틀로 복구
            $('#infoName').addClass('on').siblings().removeClass('on');
            $('.step_tel').removeClass('on');
            $('.step_captcha').removeClass('on');
        }
    });

    // 생년월일에 대한 처리
    $('.myNum').on('keyup', function (e) {
        if ($('.step_tel').hasClass('on') === false) {
            if ($('#myNum1').val().length === 6 && $('#myNum2').val().length === 1) {
                $('.step_tel').addClass('on')
                $('#infoTel').addClass('on').siblings().removeClass('on');
            }
        }
    });

    // 휴대폰 번호에 대한 처리
    $('#mobileNo').on('keyup', function (e) {
        const val = $(this).val();
        if (val.length === 11) {
            if ($("#captchaAnswer").length > 0) {
                if (!$('.step_captcha').hasClass('on')) {
                    $('.step_captcha').addClass('on');
                    $('#infoCode').addClass('on').siblings().removeClass('on');
                }
            } else {
                if (!$('#infoRe').hasClass('on')) {
                    $('#infoRe').addClass('on').siblings().removeClass('on');
                    $('.btnSubmit').addClass('show');
                }
            }
        } else {
            // 11자리가 아니면 다음 단계들을 숨기고 현재 단계 타이틀로 복구
            $('.btnSubmit').removeClass('show');
            $('.step_captcha').removeClass('on');
            $('#infoTel').addClass('on').siblings().removeClass('on');
        }
    });

    // 보안 문자 대한 처리
    $('#captchaAnswer').on('keyup', function (e) {
        const val = $(this).val();
        if (val.length === 6) {
            if (!$('#infoRe').hasClass('on')) {
                $('#infoRe').addClass('on').siblings().removeClass('on');
                $('.btnSubmit').addClass('show');
            }
        } else {
            // 6자리가 아니면 확인 타이틀을 끄고 보안문자 입력 타이틀로 복구
            $('.btnSubmit').removeClass('show');
            $('#infoCode').addClass('on').siblings().removeClass('on');
        }
    });

    // 보안 문자 대한 처리
    $('#certCode').on('keydown', function (e) {
        if (e.keyCode !== 8 && e.keyCode !== 16 && e.keyCode !== 9) {
            // number 타입에 대한 길이 값 조정
            if ($(this).attr("type") === 'number' && $(this).val().length === 6) {
                return false;
            }
        }
    });

    //문자인증번호 확인 재발송 / 확인 버튼 이벤트
    $('#certCode.resend').on('keyup', function (){
        // number 타입에 대한 길이 값 조정
        if ($(this).attr("type")  === 'number' && $(this).val().length > 6) $(this).val($(this).val().slice(0, 6));

        if($(this).val().length === 6) {
            $('.btn_box').children('.btn_check').css('visibility','visible');
            $('.btn_code').css('display','none');
            $('.btn_code').attr('aria-hidden','false');
            $('.btn_check').attr('aria-hidden','true');
        } else {
            $('.btn_box').children('.btn_check').css('visibility','hidden');
            $('.btn_code').css('display','flex');
            $('.btn_code').attr('aria-hidden','true');
            $('.btn_check').attr('aria-hidden','false');
        }
    });

    //deep link 문자 클릭 이벤트
    $('.link_num').click(function(){
        $(this).addClass('on').siblings().removeClass('on');
    });
})

function uiMethodScriptProc(uiScriptFlag) {
    if (uiScriptFlag === 'NON') {
        $(".cert_content .group_bottom").addClass("on")
        $('.btn_pass').addClass('show');
    }
}

function uiCertScriptProc(uiScriptFlag) {
    if (uiScriptFlag === 'NON' || uiScriptFlag === 'INIT') {
        if ($('.step_id').length > 0) $('.step_id').addClass('on');
        if ($('.step_captcha').length > 0) $('.step_captcha').addClass('on');
        $('.step_tel').addClass('on');

        // 상단 타이틀
        $('#infoRe').addClass('on').siblings().removeClass('on');

        // 데이터가 있는 경우 숨기기
        labelHide($("#myNum1"));
        labelHide($("#myNum2"));
        labelHide($("#userName"));
        labelHide($("#mobileNo"));

        // 버튼 변경
        $('.btnUserName').removeClass('btnUserName').addClass('btnSubmit').addClass('show');
    }
}

function labelHide(obj) {
    if (obj.length > 0) {
        if (obj.val().length > 0) {
            obj.siblings('label').addClass('hide');
        }
    }
}

// 하이픈을 입력하지 못하도록 하는 함수
function disallowHyphen(event) {
    console.log("disallowHyphen");
    var key = event.key || event.keyCode;
    console.log("event.key:"+event.key);
    console.log("event.keyCode:"+event.keyCode);

    if (key === '-') {
        event.preventDefault(); // 입력 이벤트 취소
    } else if (key === '.') {
        event.preventDefault(); // 입력 이벤트 취소
    } else     if (key === '+') {
        event.preventDefault(); // 입력 이벤트 취소
    }
}

function checkValueLayer(obj, msg) {
    if (obj.val().trim() === "") {
        messageLayerOpen("알림", msg, obj);
        return false;
    }
    return true;
}

function checkRegExpLayer(obj, type, msg) {
    const val = obj.val().trim();
    let reg;
    if (type === "NAME") {
        reg = /^[가-힣a-zA-Z]{2,20}$/;
    } else if (type === "MOBILENO") {
        reg = /^01[016789][0-9]{7,8}$/;
    }
    
    if (reg && !reg.test(val)) {
        messageLayerOpen("알림", msg, obj);
        return false;
    }
    return true;
}