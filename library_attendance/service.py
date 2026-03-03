from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Any

from library_attendance.db import db_cursor

DUPLICATE_COOLDOWN_SECONDS = 10
LIBRARY_OPENING_TIME = time(hour=9, minute=0)


@dataclass
class ScanResult:
    status: str
    message: str
    data: dict[str, Any]


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def process_scan(rfid_uid: str, device_id: str, scanned_at: datetime | None = None) -> ScanResult:
    scanned_at = scanned_at or datetime.now()

    with db_cursor() as cur:
        student = cur.execute(
            "SELECT id, roll_no, full_name FROM students WHERE rfid_uid = ?",
            (rfid_uid,),
        ).fetchone()
        if not student:
            return ScanResult("rejected", "Unknown RFID card.", {"rfid_uid": rfid_uid})

        last_scan = cur.execute(
            """
            SELECT action, scanned_at
            FROM scan_events
            WHERE student_id = ?
            ORDER BY scanned_at DESC
            LIMIT 1
            """,
            (student["id"],),
        ).fetchone()

        if last_scan:
            delta = (scanned_at - _parse_iso(last_scan["scanned_at"]))
            if delta.total_seconds() < DUPLICATE_COOLDOWN_SECONDS:
                return ScanResult(
                    "ignored",
                    "Duplicate tap ignored.",
                    {
                        "student": dict(student),
                        "duplicate_within_seconds": DUPLICATE_COOLDOWN_SECONDS,
                    },
                )

        action = "IN" if not last_scan or last_scan["action"] == "OUT" else "OUT"
        is_late = int(action == "IN" and scanned_at.time() > LIBRARY_OPENING_TIME)

        cur.execute(
            """
            INSERT INTO scan_events (student_id, device_id, action, scanned_at, is_late)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student["id"], device_id, action, scanned_at.isoformat(), is_late),
        )

    return ScanResult(
        "ok",
        f"{action} recorded for {student['full_name']}",
        {
            "student": dict(student),
            "action": action,
            "scanned_at": scanned_at.isoformat(),
            "is_late": bool(is_late),
        },
    )


def get_live_feed(limit: int = 20) -> list[dict[str, Any]]:
    with db_cursor() as cur:
        rows = cur.execute(
            """
            SELECT se.id, s.roll_no, s.full_name, se.device_id, se.action, se.scanned_at, se.is_late
            FROM scan_events se
            JOIN students s ON s.id = se.student_id
            ORDER BY se.scanned_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_daily_report(report_date: str) -> dict[str, Any]:
    with db_cursor() as cur:
        rows = cur.execute(
            """
            SELECT s.roll_no, s.full_name, se.action, se.scanned_at, se.is_late
            FROM scan_events se
            JOIN students s ON s.id = se.student_id
            WHERE date(se.scanned_at) = date(?)
            ORDER BY s.roll_no, se.scanned_at
            """,
            (report_date,),
        ).fetchall()

    sessions: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row["roll_no"]
        sessions.setdefault(
            key,
            {
                "roll_no": row["roll_no"],
                "full_name": row["full_name"],
                "entries": [],
                "exits": [],
                "late_entries": 0,
            },
        )
        if row["action"] == "IN":
            sessions[key]["entries"].append(row["scanned_at"])
            sessions[key]["late_entries"] += row["is_late"]
        else:
            sessions[key]["exits"].append(row["scanned_at"])

    return {
        "date": report_date,
        "total_visitors": len(sessions),
        "records": list(sessions.values()),
    }
