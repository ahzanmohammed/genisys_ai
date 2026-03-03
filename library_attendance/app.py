from __future__ import annotations

from datetime import date, datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from library_attendance.db import init_db, seed_demo_students
from library_attendance.service import get_daily_report, get_live_feed, process_scan

app = FastAPI(title="Smart Library Attendance")
templates = Jinja2Templates(directory="library_attendance/templates")


class ScanPayload(BaseModel):
    rfid_uid: str
    device_id: str
    timestamp: datetime | None = None


@app.on_event("startup")
def startup() -> None:
    init_db()
    seed_demo_students()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "today": date.today().isoformat()},
    )


@app.post("/api/scan")
def scan_card(payload: ScanPayload):
    result = process_scan(payload.rfid_uid, payload.device_id, payload.timestamp)
    if result.status == "rejected":
        raise HTTPException(status_code=404, detail=result.message)
    return result.__dict__


@app.get("/api/live")
def live_feed(limit: int = 20):
    return {"events": get_live_feed(limit=limit)}


@app.get("/api/report/daily")
def daily_report(report_date: str | None = None):
    report_date = report_date or date.today().isoformat()
    return get_daily_report(report_date)
