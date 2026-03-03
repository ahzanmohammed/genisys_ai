# genisys_ai

This repository now includes a complete starter implementation of a **Smart Automatic Library Attendance System** using:

- RFID card UID scans (hardware integration sample included)
- FastAPI backend APIs
- SQLite database
- Real-time admin dashboard
- Entry/exit auto-toggle logic
- Duplicate tap prevention
- Late-entry tracking
- Daily reporting

## Project Structure

- `library_attendance/app.py` - FastAPI server + dashboard routes
- `library_attendance/service.py` - attendance business logic
- `library_attendance/db.py` - DB schema and seed data
- `library_attendance/templates/dashboard.html` - admin UI
- `library_attendance/firmware/esp32_rfid_example.ino` - ESP32 + RC522 sample firmware
- `tests/test_attendance_service.py` - logic tests

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn library_attendance.app:app --reload
```

Open dashboard at: `http://127.0.0.1:8000`

## API Examples

### RFID scan

```bash
curl -X POST http://127.0.0.1:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"rfid_uid":"A1B2C3D4","device_id":"LIB_GATE_1"}'
```

### Live feed

```bash
curl http://127.0.0.1:8000/api/live
```

### Daily report

```bash
curl "http://127.0.0.1:8000/api/report/daily?report_date=2026-01-01"
```

## Notes for Hardware

Use `library_attendance/firmware/esp32_rfid_example.ino` and update:
- WiFi SSID/password
- Backend server IP
- Device ID

Then flash to ESP32 and connect RC522 over SPI.
