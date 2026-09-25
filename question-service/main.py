from fastapi import FastAPI, HTTPException

app = FastAPI(title="Exam Coach - Question Service")

questions = [
    {
        "id": 1,
        "question": "MSA의 의미는 무엇인가요?",
        "choices": [
            "Multiple Server Application",
            "Microservices Architecture",
            "Main System Architecture",
            "Managed Service API",
        ],
        "correct_answer": 2,
    },
    {
        "id": 2,
        "question": "FastAPI는 어떤 언어의 웹 프레임워크인가요?",
        "choices": ["Java", "Python", "JavaScript", "Go"],
        "correct_answer": 2,
    },
    {
        "id": 3,
        "question": "Docker 컨테이너를 여러 개 정의하고 함께 실행할 때 사용할 수 있는 도구는?",
        "choices": ["Docker Compose", "SQLite", "Git", "Pydantic"],
        "correct_answer": 1,
    },
]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/questions")
def get_questions():
    return questions


@app.get("/questions/{question_id}")
def get_question(question_id: int):
    for question in questions:
        if question["id"] == question_id:
            return question

    raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다")