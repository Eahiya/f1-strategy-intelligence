import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.websocket import router as websocket_router


def _wait_for_message(ws, expected_type: str, timeout_s: float = 10.0):
    """Read websocket messages until the expected type is received."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        message = ws.receive_json()
        if message.get("type") == expected_type:
            return message
    raise AssertionError(f"Timed out waiting for message type: {expected_type}")


def test_pit_action_keeps_race_loop_running():
    """
    Regression test for pit-stop freeze bug.

    Validates RUNNING -> PITTING -> RUNNING transition and continued lap updates.
    """
    app = FastAPI()
    app.include_router(websocket_router)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/test-pit-lifecycle") as ws:
            ws.send_json({
                "type": "init",
                "data": {
                    "circuit": "monza",
                    "total_laps": 8,
                    "scenario": "normal",
                    "weather": "dry",
                    "speed": 1.0,
                },
            })
            _wait_for_message(ws, "race_init", timeout_s=10.0)

            ws.send_json({"type": "start_race", "data": {}})
            _wait_for_message(ws, "race_status", timeout_s=5.0)

            first_lap = _wait_for_message(ws, "lap_update", timeout_s=8.0)
            assert first_lap["data"]["lap"] >= 1

            ws.send_json({"type": "action", "data": {"action": "PIT_MEDIUM", "context": {}}})

            saw_pitting = False
            saw_running_after_pit = False
            pit_lap = None
            lap_after_pit = None

            for _ in range(15):
                msg = ws.receive_json()
                msg_type = msg.get("type")
                data = msg.get("data", {})

                if msg_type == "race_status" and data.get("status") == "PITTING":
                    saw_pitting = True
                elif msg_type == "pit_stop":
                    pit_lap = data.get("lap")
                    assert data.get("compound") == "medium"
                elif msg_type == "race_status" and data.get("status") == "RUNNING":
                    if saw_pitting:
                        saw_running_after_pit = True
                elif msg_type == "lap_update" and pit_lap is not None:
                    if data.get("lap", 0) > pit_lap:
                        lap_after_pit = data.get("lap")
                        break

            assert saw_pitting, "Race never entered PITTING state after pit action"
            assert saw_running_after_pit, "Race never returned to RUNNING after pitting"
            assert pit_lap is not None, "No pit_stop payload received"
            assert lap_after_pit is not None, "No lap_update received after pit completion"

            ws.send_json({"type": "stop_race", "data": {}})
