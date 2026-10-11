#Phan 1

from __future__ import annotations
import logging
from fastapi import FastAPI, HTTPException, Query, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .database import engine
from .schemas import EnrollmentCreate

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CourseHub API",
    version="0.3.0",
    description="API thuc hanh Buoi 3 Co so du lieu Web va he thong thong tin",
)

@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "CourseHub API dang hoat dong"}

@app.get("/health")
def health_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.exception("Khong ket noi duoc co so du lieu")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Khong ket noi duoc co so du lieu",
        ) from exc
    return {"status": "ok", "database": "connected"}

#Phan 2A

@app.get("/courses")
def list_courses(
    q: str | None = Query(default=None, min_length=1),
) -> list[dict[str, object]]:
    sql = """
        SELECT code, name, credits
        FROM courses
    """
    parameters: dict[str, object] = {}

    if q is not None:
        keyword = q.strip().lower()
        if not keyword:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tu khoa tim kiem khong duoc rong",
            )
        sql += """
            WHERE LOWER(code) LIKE :keyword
            OR LOWER(name) LIKE :keyword
        """
        parameters["keyword"] = f"%{keyword}%"

    sql += " ORDER BY code"

    with engine.connect() as connection:
        rows = connection.execute(text(sql), parameters).mappings().all()
    return [dict(row) for row in rows]

#Phan 2B

@app.get("/courses/{course_code}")
def get_course(course_code: str) -> dict[str, object]:
    sql = """
        SELECT code, name, credits
        FROM courses
        WHERE code = :course_code
    """
    with engine.connect() as connection:
        row = connection.execute(
            text(sql),
            {"course_code": course_code.upper()},
        ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Khong tim thay hoc phan",
        )
    return dict(row)

#Phan 3A

@app.get("/sections")
def list_sections(
    available_only: bool = False,
) -> list[dict[str, object]]:
    sql = """
            SELECT class_id, course_code, capacity, enrolled, remaining
            FROM v_section_summary
        """
    if available_only:
        sql += " WHERE remaining > 0"
    
    sql += " ORDER BY class_id"

    with engine.connect() as connection:
        rows = connection.execute(text(sql)).mappings().all()

    return [dict(row) for row in rows]

#Phan 3B

@app.get("/students/{student_id}/enrollments")
def list_student_enrollments(student_id: str) -> list[dict[str, object]]:
    student_sql = "SELECT id FROM students WHERE id = :student_id"
    enrollment_sql = """
        SELECT e.student_id,
                s.name AS student_name,
                cs.id AS class_section_id,
                c.code AS course_code,
                c.name AS course_name,
                e.registered_at
        FROM enrollments AS e
        JOIN students AS s ON s.id = e.student_id
        JOIN class_sections AS cs ON cs.id = e.class_section_id
        JOIN courses AS c ON c.code = cs.course_code
        WHERE e.student_id = :student_id
        ORDER BY cs.id
    """
    with engine.connect() as connection:
        student = connection.execute(
            text(student_sql),
            {"student_id": student_id},
        ).first()

        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay sinh vien",
            )
        rows = connection.execute(
            text(enrollment_sql),
            {"student_id": student_id},
        ).mappings().all()

    return [dict(row) for row in rows]

#Phan 4A

@app.post(
"/enrollments",
status_code=status.HTTP_201_CREATED,
)
def create_enrollment(payload: EnrollmentCreate) -> dict[str, str]:
    student_sql = "SELECT id FROM students WHERE id = :student_id"
    section_sql = """
        SELECT cs.id,
            cs.capacity,
            COUNT(e.student_id) AS enrolled
        FROM class_sections AS cs
        LEFT JOIN enrollments AS e ON e.class_section_id = cs.id
        WHERE cs.id = :class_section_id
        GROUP BY cs.id, cs.capacity
    """
    duplicate_sql = """
        SELECT 1
        FROM enrollments
        WHERE student_id = :student_id
            AND class_section_id = :class_section_id
    """
    insert_sql = """
        INSERT INTO enrollments (student_id, class_section_id)
        VALUES (:student_id, :class_section_id)
    """
    parameters = {
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }

    with engine.begin() as connection:
        student = connection.execute(
            text(student_sql),
            {"student_id": payload.student_id},
        ).first()
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay sinh vien",
            )

        section = connection.execute(
            text(section_sql),
            {"class_section_id": payload.class_section_id},
        ).mappings().first()

        if section is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay lop hoc phan",
            )
        
        duplicated = connection.execute(
            text(duplicate_sql),
            parameters,
        ).first()

        if duplicated is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Sinh vien da dang ky lop nay",
            )
        
        if int(section["enrolled"]) >= int(section["capacity"]):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lop hoc phan da het cho",
            )
        
        connection.execute(text(insert_sql), parameters)

    return {
        "message": "Dang ky thanh cong",
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }

#Phan 5
@app.delete(
    "/enrollments/{student_id}/{class_section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_enrollment(student_id: str, class_section_id: str) -> Response:
    sql = """
        DELETE FROM enrollments
        WHERE student_id = :student_id
        AND class_section_id = :class_section_id
    """

    with engine.begin() as connection:
        result = connection.execute(
            text(sql),
            {
                "student_id": student_id,
                "class_section_id": class_section_id,
            },
        )
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay dang ky can huy",
            )
    return Response(status_code=status.HTTP_204_NO_CONTENT)




#Bài tập tự thực hành 

#Bài 1
@app.get("/lecturers")
def list_lecturers(
    available_only: bool = False,
) -> list[dict[str, object]]:
    sql = """
        SELECT id, name
        FROM lecturers
        ORDER BY id;
    """

    with engine.connect() as connection:
            rows = connection.execute(text(sql)).mappings().all()
    
    return [dict(row) for row in rows]


#Bài 2
@app.get("/sections/{section_id}")
def get_sections(section_id: str) -> dict[str, object]:
    sql = """
        SELECT cs.id AS section_id,
            cs.course_code AS course_code,
            c.name AS course_name,
            s.name AS semester_name,
            l.name AS lecturer,
            v.capacity AS capacity,
            v.enrolled AS enrolled,
            v.remaining AS remaining
        FROM class_sections cs JOIN courses c ON cs.course_code = c.code
        JOIN semesters s ON cs.semester_code = s.code
        JOIN lecturers l ON cs.lecturer_id = l.id
        JOIN v_section_summary v ON cs.id = v.class_id
        WHERE cs.id = :section_id
    """
    with engine.connect() as connection:
        row = connection.execute(
            text(sql),
            {"section_id": section_id.upper()},
        ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Khong tim thay lop cua hoc phan",
        )
    return dict(row)


#Bài 3
@app.patch("/sections/{section_id}/capacity")
def capacity_update(section_id: str, payload: dict) -> dict[str, object]:

    new_capacity = payload.get("capacity")
    if not isinstance(new_capacity, int) or new_capacity <= 0:
        raise HTTPException(
                        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail = "capacity phai lon hon 0",
        )


    sql = """
        SELECT capacity, enrolled
        FROM v_section_summary
        WHERE class_id = :section_id
    """

    with engine.connect() as connection:
        row = connection.execute(
            text(sql),
            {"section_id" : section_id.upper()}
        ).mappings().first()

        if (row is None):
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "khong tim thay hoc phan",
            )

        if new_capacity < row["enrolled"]:
            raise HTTPException(
                status_code = status.HTTP_409_CONFLICT,
                detail = f"{new_capacity} nho hon so da dang ky {row["enrolled"]}"
            )

        update = """
            UPDATE class_sections
            SET capacity = :new_capacity
            WHERE id = :section_id
        """
        connection.execute(
            text(update),
            {
                "new_capacity" : new_capacity,
                "section_id" : section_id.upper()
            }
        )
        connection.commit()
        return {"message": "Cap nhat thanh cong", "new_capacity": new_capacity}

#Bài 4
@app.get("/courses")
def list_courses(
    q: str | None = None, 
    skip: int = 0,
    limit: int = 10) -> list[dict[str, object]]:

    if skip < 0:
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = "skip khong duoc am"
        )
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = "limit phai nam trong khoang tu 1 den 100"
        )

    sql = """
        SELECT code, name, credits
        FROM courses
    """
    params = {"skip": skip, "limit": limit}
    
    if q:
        sql += " WHERE code ILIKE :keyword OR name ILIKE :keyword"
        params["keyword"] = f"%{q}%"
        
    sql += " ORDER BY code OFFSET :skip LIMIT :limit"
    
    with engine.connect() as connection:
        rows = connection.execute(text(sql), params).mappings().all()
        return [dict(row) for row in rows]