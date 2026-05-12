"""
Hybrid Edge-to-Cloud Visual Intelligence
Worker Operational Safety System — Configuration
"""

# ─── Server ──────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 5000
DEBUG = True
SECRET_KEY = "worker-safety-intel-2026"

# ─── Simulation Tick Rate (ms) ───────────────────────────
SENSOR_TICK_MS = 1000          # Environmental sensors update every 1s
VISION_TICK_MS = 800           # Camera AI inference every 0.8s
WORKER_TICK_MS = 500           # Worker position update every 0.5s
EDGE_METRICS_TICK_MS = 2000    # Edge compute metrics every 2s

# ─── Factory Floor (virtual grid) ────────────────────────
FLOOR_WIDTH = 800
FLOOR_HEIGHT = 600

# ─── Hazardous Zones ─────────────────────────────────────
ZONES = [
    {
        "id": "zone_A",
        "name": "Heavy Machinery Area",
        "type": "danger",
        "x": 50, "y": 50, "w": 200, "h": 180,
        "color": "#ff4444",
        "max_workers": 2,
        "required_ppe": ["helmet", "vest", "goggles", "gloves"]
    },
    {
        "id": "zone_B",
        "name": "Chemical Storage",
        "type": "restricted",
        "x": 550, "y": 50, "w": 200, "h": 180,
        "color": "#ff8800",
        "max_workers": 1,
        "required_ppe": ["helmet", "vest", "goggles", "gloves", "respirator"]
    },
    {
        "id": "zone_C",
        "name": "Assembly Line",
        "type": "caution",
        "x": 50, "y": 370, "w": 300, "h": 180,
        "color": "#ffcc00",
        "max_workers": 4,
        "required_ppe": ["helmet", "vest"]
    },
    {
        "id": "zone_D",
        "name": "Loading Dock",
        "type": "caution",
        "x": 500, "y": 370, "w": 250, "h": 180,
        "color": "#ffcc00",
        "max_workers": 3,
        "required_ppe": ["helmet", "vest", "gloves"]
    },
    {
        "id": "zone_safe",
        "name": "Safe Corridor",
        "type": "safe",
        "x": 280, "y": 240, "w": 240, "h": 120,
        "color": "#00cc66",
        "max_workers": 10,
        "required_ppe": []
    }
]

# ─── Edge Camera Nodes ───────────────────────────────────
EDGE_CAMERAS = [
    {"id": "cam_1", "name": "Edge-Cam North", "x": 150, "y": 30,  "fov_radius": 220, "zone": "zone_A"},
    {"id": "cam_2", "name": "Edge-Cam East",  "x": 650, "y": 30,  "fov_radius": 220, "zone": "zone_B"},
    {"id": "cam_3", "name": "Edge-Cam South-W","x": 200, "y": 520, "fov_radius": 250, "zone": "zone_C"},
    {"id": "cam_4", "name": "Edge-Cam South-E","x": 625, "y": 520, "fov_radius": 220, "zone": "zone_D"},
]

# ─── Workers ─────────────────────────────────────────────
WORKERS = [
    {"id": "W001", "name": "Rajesh Kumar",    "role": "Machine Operator",   "shift": "Day"},
    {"id": "W002", "name": "Priya Sharma",    "role": "Quality Inspector",  "shift": "Day"},
    {"id": "W003", "name": "Ahmed Khan",      "role": "Chemical Handler",   "shift": "Day"},
    {"id": "W004", "name": "Sneha Patel",     "role": "Assembly Tech",      "shift": "Day"},
    {"id": "W005", "name": "Vikram Singh",    "role": "Forklift Operator",  "shift": "Day"},
    {"id": "W006", "name": "Neha Gupta",      "role": "Safety Supervisor",  "shift": "Day"},
]

# ─── PPE Items ───────────────────────────────────────────
PPE_ITEMS = ["helmet", "vest", "goggles", "gloves", "respirator", "boots"]

# ─── Environmental Sensor Thresholds ─────────────────────
SENSOR_THRESHOLDS = {
    "temperature":  {"unit": "°C",   "min": 15,  "max": 45,  "warn": 38,  "critical": 42},
    "humidity":     {"unit": "%",    "min": 20,  "max": 90,  "warn": 75,  "critical": 85},
    "gas_co":       {"unit": "ppm",  "min": 0,   "max": 100, "warn": 35,  "critical": 50},
    "gas_h2s":      {"unit": "ppm",  "min": 0,   "max": 50,  "warn": 10,  "critical": 20},
    "noise":        {"unit": "dB",   "min": 30,  "max": 120, "warn": 85,  "critical": 100},
    "vibration":    {"unit": "mm/s", "min": 0,   "max": 30,  "warn": 15,  "critical": 25},
    "dust_pm25":    {"unit": "µg/m³","min": 0,   "max": 200, "warn": 75,  "critical": 150},
}

# ─── Alert Severity Levels ───────────────────────────────
ALERT_LEVELS = {
    "info":     {"priority": 0, "color": "#4fc3f7"},
    "low":      {"priority": 1, "color": "#81c784"},
    "medium":   {"priority": 2, "color": "#ffb74d"},
    "high":     {"priority": 3, "color": "#ff8a65"},
    "critical": {"priority": 4, "color": "#ef5350"},
}

# ─── Edge Computing Simulation ───────────────────────────
EDGE_NODE_SPECS = {
    "processor": "NVIDIA Jetson Nano (Simulated)",
    "ram_gb": 4,
    "gpu_cores": 128,
    "max_fps": 30,
    "model": "YOLOv8-nano (Simulated)",
    "inference_time_ms_range": (18, 45),
    "power_watts_range": (5, 15),
}

CLOUD_SPECS = {
    "provider": "AWS IoT Core (Simulated)",
    "region": "ap-south-1",
    "latency_ms_range": (50, 200),
    "bandwidth_mbps": 100,
}
