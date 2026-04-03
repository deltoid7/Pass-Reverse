const _layerFocusTarget = {};
const _layerOnList = [];

$(function () {
    // 본인확인 이용 동의 체크박스 팝업 열기
    $("#btnAgreeItemLayerOpen").click(function () {
        openLayer('agreeItemLayer', $(this));
    });

    // 알뜰폰 사업자 안내 팝업창 열기
    $("#btnMvnoCompanyLayerOpen").click(function () {
        openLayer('mvnoCompanyLayer', $(this));
    });

    // 인증 가이드 팝업창 열기
    $("#btnCertGuideLayerOpen").click(function () {
        openLayer('certGuideLayer', $(this));
    });

    // (공통) 팝업창 닫기
    $('.popup_wrap .btnLayerClose').click(function () {
        closeLayer($(this));
    });
})

// 공통 레이어 열기
function openLayer(targetId, focusTarget) {
    let target = '#'+targetId+'.popup_wrap';
    _layerFocusTarget[targetId] = focusTarget;
    _layerOnList.push(target);

    $(target).addClass("on");
    if (targetId === 'agreeContLayer') {
        $(target).find('.content_inner').prop("tabindex", "0");
    }

    // 레이어 포커스
    let firstFocus = focusNotBack(target);
    if (Object.keys(_layerFocusTarget).length === 1) {
        // 메인 컨텐츠 영역 숨기기 - 리더기 기준
        agreeLayerHiddenTag('open');
    } else {
        if (_layerOnList.length >= 2) {
            let popTarget = _layerOnList[_layerOnList.length-2]
            $(popTarget).attr('aria-hidden', true);
            $(popTarget).attr('inert', '');
        }
    }

    // 포커스를 위해 시간차 (스크롤 방지)
    setTimeout(function () {
        if (firstFocus && firstFocus.length > 0) {
            firstFocus[0].focus({ preventScroll: true });
        }
    }, 50);
}

// 공통 레이어 닫기
function closeLayer(target) {
    // 메인 컨텐츠 영역 보이기 - 리더기 기준
    if (Object.keys(_layerFocusTarget).length === 1) {
        agreeLayerHiddenTag('close');
    } else {
        if (_layerOnList.length >= 2) {
            let popTarget = _layerOnList[_layerOnList.length-2]
            $(popTarget).removeAttr('inert');
            $(popTarget).attr('aria-hidden', false);
        }
    }

    const targetId = target.parents('.popup_wrap').attr('id');
    if (targetId === 'agreeContLayer') {
        $('#agreeContLayer.popup_wrap .content_inner').scrollTop(0);
        $('#agreeContLayer.popup_wrap .content_inner').prop("tabindex", "-1");
    }
    target.parents('.popup_wrap').removeClass("on");

    // 포커스를 위해 시간차 (스크롤 방지)
    setTimeout(function () {
        if (_layerFocusTarget[targetId] !== '' && _layerFocusTarget[targetId] !== undefined && _layerFocusTarget[targetId] !== null) {// 팝업 포커스 처리
            if (_layerFocusTarget[targetId].length > 0) {
                _layerFocusTarget[targetId][0].focus({ preventScroll: true });
            }
            delete _layerFocusTarget[targetId];
            _layerOnList.pop();
        }
    }, 50);
}

// (공통) 알림메세지 팝업창
function messageLayerOpen(title, message, focusTarget) {
    // 알림 타이틀
    $('#messageLayer .popup_head h3').html(title);

    // 상세 메세지
    if (message !== null && message !== '') {
        $('#messageLayer .popup_content p').html(message);
        $('#messageLayer .popup_content').show();
    } else $('#messageLayer .popup_content').hide();

    // 레이어 팝업 열기
    openLayer('messageLayer', focusTarget);

    return false;
}

// 포커스
function focusNotBack(target) {
    let focusList = $(target).find('a, button');
    let firstFocus = focusList.eq(0);
    let lastFocus = focusList.eq(focusList.length - 1);
    $(target).on({
        'keydown' : function(e) {
            // 현재 포커스 정보
            let active = $(document.activeElement);

            // 첫번째 포커스 대상
            if(active.is(firstFocus)) {
                if (e.shiftKey && e.keyCode === 9) {
                    e.preventDefault();
                    $(lastFocus).focus();
                }
            }

            // 마지막 포커스 대상
            if (active.is(lastFocus)) {
                if (!e.shiftKey && e.keyCode === 9) {
                    e.preventDefault();
                    $(firstFocus).focus();
                }
            }
        }
    })

    return firstFocus;
}

// 레이어팝업 외 정보를 스크린리더기가 읽지 않도록 숨김 처리
function agreeLayerHiddenTag(flag) {
    let $target = $('header, section, footer');
    // 웹접근성을 처리를 위한 LAYER OFF
    if (flag === 'open') {
        $('body').addClass("ovf_hide");
        $target.attr('aria-hidden', true);
        $target.attr('inert', '');
    } else if (flag === 'close') {
        $('body').removeClass("ovf_hide");
        $target.attr('aria-hidden', false);
        $target.removeAttr('inert', '');
    }
}