import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "coursehub")
os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_password")

from backend.app.main import app

REQUIRED_PATHS = {
    "/health",
    "/courses",
    "/sections",
    "/students/{student_id}/enrollments",
    "/enrollments",
    "/enrollments/{student_id}/{class_section_id}",
}


def test_required_paths_are_registered():
    paths = set(app.openapi()["paths"])
    missing = REQUIRED_PATHS - paths
    assert not missing, f"Missing API paths: {sorted(missing)}"


def test_enrollment_methods_are_registered():
    paths = app.openapi()["paths"]
    assert "get" in paths["/sections"]
    assert "post" in paths["/enrollments"]
    assert "delete" in paths[
        "/enrollments/{student_id}/{class_section_id}"
    ]