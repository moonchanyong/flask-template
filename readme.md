[![pipeline status](https://gitlab.com/deepscent/server/badges/master/pipeline.svg)](https://gitlab.com/deepscent/server/commits/master)
[![coverage report](https://gitlab.com/deepscent/server/badges/master/coverage.svg)](https://gitlab.com/deepscent/server/commits/master)

# Overview
 아롬 앱의 백엔드 서버 프로젝트입니다. 파이썬 3.6.x로 작성되었으며 백엔드 서비스로 AWS와 Mongo DB를 사용합니다.

# 선행 지식과 요구사항
 이 문서는 독자가 아래와 같은 선행 지식이 있다는 가정하에 작성 되었습니다.

 * Python에 대한 기본 지식
   - unittest 패키지
 * Virtualenv와 같은 Python 개발 환경에 대한 기본 지식
 * Flask 기본
 * AWS 기본
 * RESTful API

## 개발환경 요구사항

 * Python 3.6.x
 * 개발용 Mongo DB가 설치 되어 있을 것.
 * 충분한 AWS 권한 (S3, Lambda, API Gateway, SES, EC2 등)이 있는 AWS 계정의 ACCESS_KEY,
   SECRET_KEY가 ~/.aws/credentials에 설정 되어 있을 것.


## 사용 중인 AWS 서비스

 * S3: Deploy와 서버 버전 관리, 이미지 업로드 서버로 사용됨.
 * Lambda, API Gateway: Serverless 아키텍처로 서버를 서비스 하기 위해 사용됨.
 * EC2: Mongo DB를 호스팅하기 위해서 사용
 * SES: 메일을 보내기 위한 서비스로 사용
 * AWS IoT: 디바이스 정보열람, 제어를 위해 사용

# 프로젝트 구조

 * manage.py : 관리용 스크립트.
 * requirements.txt : 사용 중인 python package를 명시하는 파일
 * words.txt : 임시 암호 생성에 쓰이는 단어들이 들어있는 파일
 * main.py : entry point. 개발용 서버를 띄우거나, WSGI 인터페이스를 서비스용 서버에 제공하는 용도
 * zappa_settings.json : Serverless 배포를 위해 사용하는 툴인 'zappa'의 설정 파일.
 * .gitlab-ci.yml : gitlab 서버에 푸시할 때마다 실행되는 CI에 대한 설정 파일.
 * tests/ : 테스트가 들어있는 폴더.
   - \_\_init\_\_.py : 테스트 패키지의 init 파일. 여기에서 import된 테스트만 CI나 manage.py test 에서 실행됨.
 * deepscent/ : 서버 구현에 대한 코드가 들어있는 폴더
   - apitools.py : API 전반에서 사용되는 함수들이 정의 되어있음.
   - monkey_patch.py : 다른 패키지의 버그에 대한 몽키 패치가 정의 되어있음.
   - db.py : Mongo DB에서 사용하는 모델들이 정의 되어있음.
   - templates/ : 이메일 템플릿들이 들어있는 폴더

# 실행 방법
## 개발 서버 실행

미리 Mongo DB가 localhost:27017 에서 접근이 가능하도록 세팅되어있어야 합니다. 개발용 Mongo DB는 Docker 사용해서 설치하는 것을 추천하지만, 다른 방식으로 설치해도 문제는 없습니다. 만약 Mongo DB 호스트나 포트가 다르다면 deepscent/config.py 를 수정해주세요.

```bash
# 프로젝트 폴더에서 시작.
# 패키지들을 설치해 줌.
> pip install -r requirements.txt
# 개발 서버 실행
> python main.py
# http://localhost:5000/api/docs 에서 API 문서를 열람할 수 있습니다.
```

## 유닛 테스트 실행
개발 서버 실행과 마찬가지로 유닛 테스트를 실행할 때에는 Mongo DB가 접근 가능해야합니다. 유닛 테스트는 Mongo DB에 데이터를 쓰거나 지울 수 있으므로 보존해야할 데이터가 있는 Mongo DB에 연결된 상태로 유닛 테스트를 실행해서는 안됩니다.

```bash
# 테스트 실행
> ./manage.py test
# 만약 테스트 커버리지도 함께 확인하고 싶다면
> ./manage.py --coverage
# 특정 테스트만 실행하고 싶다면
> ./manage.py --name tests.auth
```

# Rule
## Config Rule
  - 설정은 deepscent/config.py 에 저장합니다.
  - 배포되는 환경(dev, staging, production)에 대한 정보 중, id/password 등 보안이 중요한 정보는 해당 환경의 환경변수로 지정합니다.
  - 서버 실행 시 로드할 설정은 환경변수에 따라 결정됩니다.
    - CI 환경 변수가 존재한다면 CiConfig 로드
    - DEV_SERVER 환경 변수가 존재한다면 DevServerConfig 로드

## 개발 규칙
  - API를 작성할 때에는 유닛테스트를 함께 작성합니다.
  - 테스트가 실패한다면 gitlab 저장소에 push하지 않습니다.
  - 가능한 한 높은 테스트 커버리지를 유지합니다. (80% 이상)

## API 문서화
API 문서는 http 서버의 api/docs 경로에서 확인하고 테스트해볼 수 있습니다. API 문서는 swagger를 사용해서 자동으로 생성됩니다. 이 과정을 위해 flask-restful-swagger-2 패키지를 사용하지만, 그대로 사용하기에는 아래와 같은 단점이 있습니다.

 * API 스펙에 대한 명시와 별도로 인자 파싱/체크를 해줘야합니다.
 * swagger 양식 그대로 작성하다보니 중복 내용이 많고 장황합니다.

그래서 apitools.py에 spec 함수가 있습니다. spec 함수가 제공하는 내용은 아래와 같습니다.

 * 명시한대로 API 문서를 생성해줍니다.
 * API의 Parameter를 파싱하고, 명시한 도메인에 부합하는 지 체크합니다. 만약 에러가 잘못된 인자가들어왔다면 400 에러를 발생시킵니다.

새로 API를 작성할 때에는 기존 API들과 마찬가지로 spec 함수를 사용해 문서화와 인자 파싱을 해주세요.

# 주요 데코레이터
 * @spec : API 스펙을 명시하고 이에 따라 API 문서를 자동으로 생성합니다. 인자 파싱과 체크를 하는 역할도 해줍니다.
 * @auth.check_auth : 헤더에 있는 Authroization 정보로 유저를 인증하고, 해당 유저 객체를 g.user에 넣어줍니다.
 * @device.check_device : 유저 인증과 함께, 해당 유저가 API 경로에 있는 device_id에 해당되는 디바이스에 대한 권한이 있는 지도 함께 체크해줍니다.


# 코드를 읽어볼 때 가이드
 비교적 간단한 구현이 있는 recipe.py에 있는 API들부터 읽어보는 것을 권장합니다. 아래 내용에 유의하여 읽어봅니다.

 1. API 경로별로 나뉘어져 있는 클래스
 2. 각 메소드의 명은 http request가 어떤 method로 호출되었는지를 의미함. (ex: get, post, delete, put)
 3. @spec 데코레이터의 활용
 4. @check_auth 데코레이더의 활용
 5. db Model의 사용 방법. (ex: RecipeModel)

# Device Shadow

```json
{
  "fan1": 4200,     # number, 0-4200
  "fan2": 0,        # number, 0-4200
  "fan3": 4200,     # number, 0-4200
  "fan4": 4200,     # number, 0-4200
  "light": 100,     # number, 0-100
  "power": true,    # boolean
  "owner_id": "dafslkadsjflkasd",
  "cart1_scent": "lemon",           # string, 비어있다면 null
  "cart1_serial": "jsdaakdlfjsdf",  # string, 비어있다면 null
  "cart2_scent": "lemon",
  "cart2_serial": "jsdaakdlfjsdf",
  "cart3_scent": "lemon",
  "cart3_serial": "jsdaakdlfjsdf",
  "cart4_scent": "lemon",
  "cart4_serial": "jsdaakdlfjsdf",
  "timestamp": 1290319023
}
```

