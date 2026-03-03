from datetime import datetime

from library_attendance import db
from library_attendance.service import process_scan


def setup_module():
    db.init_db()
    db.seed_demo_students()
    with db.db_cursor() as cur:
        cur.execute("DELETE FROM scan_events")


def test_in_out_toggle_and_duplicate_prevention():
    t1 = datetime(2026, 1, 1, 9, 5, 0)
    first = process_scan("A1B2C3D4", "TEST", t1)
    assert first.status == "ok"
    assert first.data["action"] == "IN"
    assert first.data["is_late"] is True

    second = process_scan("A1B2C3D4", "TEST", datetime(2026, 1, 1, 9, 5, 5))
    assert second.status == "ignored"

    third = process_scan("A1B2C3D4", "TEST", datetime(2026, 1, 1, 9, 25, 0))
    assert third.status == "ok"
    assert third.data["action"] == "OUT"
