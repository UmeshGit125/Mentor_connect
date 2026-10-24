from fastapi import APIRouter
from sqlalchemy import select

from app.deps import Db
from app.models import Student
from app.schemas import StudentIn, StudentOut

router = APIRouter(tags=["students"])


@router.post("/students", response_model=StudentOut)
def create_student(body: StudentIn, db: Db) -> Student:
    """Idempotent on email: the same email gets the same student back."""
    student = db.scalar(select(Student).where(Student.email == body.email))
    if student is None:
        student = Student(name=body.name, email=body.email)
        db.add(student)
        db.commit()
    return student
