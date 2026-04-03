<img width="160" height=auto alt="pass-reverse" src="https://raw.githubusercontent.com/deltoid7/Pass-Reverse/refs/heads/main/src/pass-reverse-logo.png" />

# Pass-Reverse
PASS(NICE 평가정보) 휴대폰 본인 인증 api를 역공학한 라이브러리입니다. (모든 인증 방식 구현, GUI 구현, 캡차 해결 모델 구현)

<br>

## 모듈 설치

```bash
pip install git+https://github.com/Imp1ex/Pass-Reverse.git
```

<br>

## 테스트 해보기
모든 테스트 파일은 examples 폴더에 있습니다.<br>
[gui를 이용하여 인증하고, callback으로 응답 받는 예제](https://github.com/Imp1ex/Pass-Reverse/blob/main/examples/web/web_callback.py)

<br>

## 감사합니다
https://github.com/shy9-29/PASS-NICE/ 에서 많은 영감을 받았었습니다.

<br>

## 추가 정보
제가 제공하는 캡차 해결 서버는 불안정합니다. ([Render.com](https://render.com/) 무료 티어를 [cron-job.org](https://cron-job.org/)에서 슬립 상태로 안들어가게 요청보내는 방식이므로)<br>
따라서 [해당 폴더](https://github.com/Imp1ex/Pass-Reverse/tree/main/pass_reverse/captcha_solver)를 참조해서 직접 서버를 구성하는 방식을 추천합니다.<br>
그리고 서버 변경 시, [여기에서](https://github.com/Imp1ex/Pass-Reverse/blob/main/pass_reverse/verification/utils/captcha_solver.py) url도 변경해야 합니다.<br>
<br>
해당 부분은 연구해보면서 보다 안정적이게 배포 가능하도록 수정해보도록 하겠습니다. (gui는 사용자 직접 입력이므로 해당 사항 없음)

<br>

## 데모

https://github.com/user-attachments/assets/33614626-27bc-4089-ac17-31622564743a
