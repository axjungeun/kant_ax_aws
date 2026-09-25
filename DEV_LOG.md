# Development Log

## 2026-09-25 — AI Exam Coach Mini MSA

### 목표

AWS Server 스터디 숙제 조건에 맞춰 기존 AI Exam Coach 아이디어의 일부를 작은 MSA 백엔드로 구현했다.

숙제 요구사항:

- Python 3.10 이상
- FastAPI
- Docker
- MSA(Microservices Architecture)
- AI를 이용한 구현 허용

이번 구현에서는 Python 3.12를 사용했다.

## 서비스 구조

```text
사용자 / Swagger
        |
        | POST /attempts
        v
Attempt Service
        |
        | HTTP
        | http://question-service:8000
        v
Question Service
```

### Question Service

역할: 문제와 정답 제공

- `GET /health`
- `GET /questions`
- `GET /questions/{question_id}`
- 로컬 포트: `8001`

### Attempt Service

역할: 답안 제출, Question Service 호출, 채점 결과 반환

- `GET /health`
- `POST /attempts`
- `GET /attempts/{attempt_id}`
- 로컬 포트: `8002`

두 서비스는 각각 독립적인 FastAPI 서버와 Docker 컨테이너로 실행한다.

## 구현 순서

1. `question-service`를 먼저 만들고 Swagger에서 `GET /questions` 200 응답을 확인했다.
2. `attempt-service`를 추가하고 HTTPX를 이용해 Question Service를 호출하도록 구성했다.
3. Docker 적용 전에는 각각 `8001`, `8002` 포트에서 FastAPI 서버를 직접 실행해 서비스 간 통신을 확인했다.
4. 각 서비스에 Dockerfile을 만들었다.
5. 루트의 `compose.yaml`에서 두 서비스를 함께 실행하도록 구성했다.
6. Docker 내부에서는 `localhost` 대신 Compose 서비스 이름인 `question-service`를 DNS 이름으로 사용했다.
7. `POST /attempts`에서 HTTP 201과 `is_correct: true`를 확인했다.

## 정상 동작 확인

요청 예시:

```json
{
  "question_id": 1,
  "selected_answer": 2
}
```

정상 응답 예시:

```json
{
  "id": "<uuid>",
  "question_id": 1,
  "selected_answer": 2,
  "correct_answer": 2,
  "is_correct": true
}
```

성공 결과 캡처는 `docs/01_msa_attempt_success_201.png`에 저장했다.

## 장애 테스트

Question Service만 중지했다.

```bash
docker compose stop question-service
```

이 상태에서 Attempt Service에 새 답안을 제출하면 Question Service에 접근할 수 없으므로 `503 Service Unavailable`이 반환되는 것을 확인했다.

이를 통해 두 서비스가 독립된 컨테이너로 실행되고, Attempt Service의 채점 기능이 Question Service에 의존한다는 점을 확인했다.

## 디버깅 기록

### 1. Dockerfile 누락

첫 Docker 빌드에서 다음 오류가 발생했다.

```text
failed to read dockerfile: open Dockerfile: no such file or directory
```

원인은 `attempt-service` 폴더에 Dockerfile이 실제로 생성되지 않은 것이었다.

`ls -la attempt-service`로 파일 존재 여부를 확인한 뒤 Dockerfile을 생성해 해결했다.

### 2. Docker에서 localhost 사용 문제

Docker 적용 전 Attempt Service는 Question Service에 다음 주소로 접근했다.

```text
http://127.0.0.1:8001
```

하지만 Docker 컨테이너에서 `localhost`는 현재 컨테이너 자신을 의미한다.

Docker Compose 내부에서는 다음 주소를 사용하도록 변경했다.

```text
http://question-service:8000
```

### 3. 소스 수정 후에도 503/404가 계속 발생

Mac의 `attempt-service/main.py`는 수정됐지만 실행 중인 Docker 컨테이너에는 이전 코드가 남아 있었다.

원본과 컨테이너 내부 파일을 각각 확인했다.

```bash
grep -n "QUESTION_SERVICE_URL" attempt-service/main.py

docker compose exec attempt-service \
  grep -n "QUESTION_SERVICE_URL" /app/main.py
```

Docker 내부 네트워크도 직접 확인했다.

```bash
docker compose exec attempt-service python -c \
"import httpx; r=httpx.get('http://question-service:8000/questions/1'); print(r.status_code); print(r.text)"
```

결과는 `200`이었기 때문에 Question Service와 Docker 네트워크는 정상임을 확인했다.

이후 Attempt Service 이미지를 캐시 없이 다시 빌드하고 컨테이너를 재생성했다.

```bash
docker compose build --no-cache attempt-service
docker compose up -d --force-recreate attempt-service
```

컨테이너 내부 코드가 `http://question-service:8000`을 사용하는 것을 확인한 뒤 다시 요청했고 최종적으로 HTTP 201과 `is_correct: true`가 정상 반환됐다.

## 이번 실습에서 확인한 핵심

- MSA는 단순히 파일을 나누는 것이 아니라 서비스를 독립적으로 실행하고 서비스 간 API 통신을 구성하는 방식이다.
- Docker 컨테이너마다 `localhost`가 별도로 존재한다.
- Docker Compose에서는 서비스 이름을 내부 DNS 이름으로 사용할 수 있다.
- 로컬 소스 수정과 실행 중인 Docker 이미지/컨테이너의 상태는 별개다.
- 코드 변경 후 필요한 경우 이미지를 재빌드하고 컨테이너를 재생성해야 한다.
- 서비스 하나를 중지해 장애 상황과 의존 관계를 직접 검증할 수 있다.

## 실행

```bash
docker compose up -d --build
docker compose ps
```

### Swagger

Docker Compose 실행 후:

- Question Service: http://localhost:8001/docs
- Attempt Service: http://localhost:8002/docs