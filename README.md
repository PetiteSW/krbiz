# KRBIZ
소상공인들을 위한 소프트웨어 기본템.

[설치방법 바로가기](#설치방법-how-to-install)

## 사용방법 (How to use)
### merge-orders
리테일 플랫폼별 주문내역을 병합해 배송 플랫폼 양식으로 변환해주는 명령어.
> 병합하는 명령어랑 변환하는 명령어를 분리하기로 마음먹었습니다. 알아두세욤.

```bash
# krbiz 가 설치되어 있는 가상환경에서
merge-orders --input-dir PATH_TO_THE_FILES
```
``PATH_TO_THE_FILES`` 를 주문내역 파일이 들어있는 폴더의 위치로 바꾸어주세요.
**해당 폴더에 들어있는 파일 중 오늘 날짜의 파일만 불러옵니다.**

해당 명령어는 ``input-dir`` 에 들어있는 모든 엑셀 파일들 중 설정파일(configuration)에서 매칭되는 모든 파일들을 찾아서 병합한 후 ``merged.xlsx`` 에 배송 플랫폼 양식에 맞게 저장합니다.

파일들 중 암호화되어 있는 파일이 있으면 암호를 요구하니 터미널 안내 메세지를 잘 살펴봐주세요.

> 결과 파일 위치를 바꿀 수 있는 옵션이 있지만 귀찮으니까 다음번 업데이트에서 설명하겠습니다.

Configuration 파일은 ``src/krbiz/_resources/_order_delivery_config_template.xlsx`` 입니다.

> 이 부분도 귀찮으니까 다음번 업데이트에서 설명하겠습니다.

## 설치방법 (How to install)

### 필요한 프로그램 설치
컴퓨터에 파이썬(`python`)과 콘다(conda), 깃(git) 명령어가 설치되어 있어야 합니다.
> python >= 3.12

### 가상환경 설정
``conda``명령어를 이용해  ``krbiz`` 를 위한 가상환경을 새로 하나 생성합니다.
```bash
conda create -n krbiz python=3.12
```

### krbiz 설치
``krbiz`` 를 깃허브에서 내려받습니다.
```bash
git clone https://github.com/YooSunYoung/krbiz.git
```

이제 ``krbiz`` 소스코드가 있는 폴더로 이동합니다.
```bash
cd krbiz
```

위에서 생성한 가상환경을 활성화해줍니다.
```bash
conda activate krbiz
```

가상환경이 활성화 된 상태에서 ``krbiz``를 설치합니다.
```bash
pip install -e .
```

> 설치 이후에는 터미널혹은 Powershell 을 열고 ```conda activate krbiz``` 명령어를 이용해 가상환경을 활성화한 후 바로 명령어들을 사용할 수 있습니다.

## 업데이트 방법 (How to update)
깃 명령어로 소스코드를 업데이트하고 가상환경에서 새롭게 설치할 수 있습니다.
```bash
conda activate krbiz
git pull origin main
pip install -e .
```

## Developer's Guide.
### Release

I didn't have any resources to automate the UI tests for now so instead
I have been doing this check manually before releasing.
#### Functionality check-list before releases.
- [ ] Order file upload.
    - [ ] When a new order file is uploaded, it should check if it can be merged or not.

- [ ] Order variable settings.
    - [ ] ``tests/order-variable-settings/missing_*.xlsx`` files should alert about
        the wrong configuration and abort the uploading.
        **These files should be warned about missing headers.**
    - [ ] ``tests/order-variable-settings/wrong_*.xlsx`` files should alert about
        the wrong configuration and abort the uploading.
        **These files should be warned about wrong dtype of mandatory columns**
    - [ ] ``tests/order-variable-settings/additional*.xlsx`` files should change    the settings accordingly.
        - [ ] Preview should be updated
        - [ ] ``현재 설정파일 내려받기`` file is same as the latest one uploaded.
    - [ ] ``초기화`` button should return the settings to the default
        - [ ] Preview should be updated
        - [ ] ``현재 설정파일 내려받기`` file is same as the default file.

- [ ] Header unification(translation)
    - [ ] When the page is loaded/refreshed, it should show the preview
          of the merged files. **Only the first rows of each file**
    - [ ] When user upload a new order-file, it should show in the preview.

TODO:
- [ ] Merge file download button
- [ ] Translated file download button
- [ ] Skip preview of the encrypted file if password doesn't work
- [ ] Validate the password as it is written
