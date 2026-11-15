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
    assert "post" in paths["/enrollments"]
    assert "delete" in paths[
        "/enrollments/{student_id}/{class_section_id}"
    ]