from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import uuid

app = FastAPI(title="Exam Coach - Attempt Service")

QUESTION_SERVICE_URL = "http://question-service:8000"

attempts = {}


class AttemptRequest(BaseModel):
    question_id: int
    selected_answer: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/attempts", status_code=201)
async def create_attempt(request: AttemptRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{QUESTION_SERVICE_URL}/questions/{request.question_id}",
                timeout=3.0,
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Question Service에 연결할 수 없습니다",
        )

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다")

    question = response.json()

    attempt_id = str(uuid.uuid4())

    result = {
        "id": attempt_id,
        "question_id": request.question_id,
        "selected_answer": request.selected_answer,
        "correct_answer": question["correct_answer"],
        "is_correct": request.selected_answer == question["correct_answer"],
    }

    attempts[attempt_id] = result

    return result


@app.get("/attempts/{attempt_id}")
def get_attempt(attempt_id: str):
    if attempt_id not in attempts:
        raise HTTPException(status_code=404, detail="풀이 기록을 찾을 수 없습니다")

    return attempts[attempt_id]