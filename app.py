"""
Hybrid Edge-to-Cloud Visual Intelligence
Worker Operational Safety System — Flask Server

Run:  python app.py
"""

import threading
import time
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from config import HOST, PORT, DEBUG, SECRET_KEY, SENSOR_TICK_MS
from iot_simulator import SimulationEngine

# ─── App Init ────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ─── Simulation Engine ──────────────────────────────────
engine = SimulationEngine()
sim_running = True

# ─── Routes ──────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/state")
def api_state():
    """REST endpoint for full simulation state."""
    return jsonify(engine.get_full_state())

@app.route("/api/alerts")
def api_alerts():
    return jsonify(engine.alerts.get_recent(50))

# ─── Socket.IO Events ───────────────────────────────────
@socketio.on("connect")
def handle_connect():
    print(f"[+] Client connected: {request.sid}")
    emit("init_state", engine.get_full_state())

@socketio.on("disconnect")
def handle_disconnect():
    print(f"[-] Client disconnected: {request.sid}")

@socketio.on("trigger_incident")
def handle_trigger_incident(data):
    incident_type = data.get("type", "gas_leak")
    engine.trigger_incident(incident_type)
    emit("incident_triggered", {"type": incident_type, "status": "ok"})
    print(f"[!] Incident triggered: {incident_type}")

@socketio.on("acknowledge_alert")
def handle_ack_alert(data):
    alert_id = data.get("id")
    if alert_id:
        engine.alerts.acknowledge(alert_id)
        emit("alert_acknowledged", {"id": alert_id})

@socketio.on("clear_alerts")
def handle_clear_alerts():
    engine.alerts.clear_all()
    emit("alerts_cleared", {"status": "ok"})

@socketio.on("toggle_camera")
def handle_toggle_camera(data):
    cam_id = data.get("camera_id")
    for cam in engine.cameras:
        if cam.id == cam_id:
            cam.is_online = not cam.is_online
            emit("camera_toggled", {"camera_id": cam_id, "is_online": cam.is_online})
            break

# ─── Background Simulation Thread ───────────────────────
def simulation_loop():
    """Runs the simulation in a background thread and pushes updates."""
    global sim_running
    tick_interval = SENSOR_TICK_MS / 1000.0
    while sim_running:
        try:
            engine.tick()
            update = engine.get_realtime_update()
            socketio.emit("realtime_update", update)
            time.sleep(tick_interval)
        except Exception as e:
            print(f"[ERROR] Simulation loop: {e}")
            time.sleep(1)

# ─── Main ────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Hybrid Edge-to-Cloud Visual Intelligence")
    print("  Worker Operational Safety System")
    print("=" * 60)
    print(f"  Dashboard: http://localhost:{PORT}")
    print(f"  API:       http://localhost:{PORT}/api/state")
    print("=" * 60)

    sim_thread = threading.Thread(target=simulation_loop, daemon=True)
    sim_thread.start()

    socketio.run(app, host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
