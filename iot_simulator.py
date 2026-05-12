"""
Hybrid Edge-to-Cloud Visual Intelligence
IoT Simulation Engine — Worker Safety Intelligence

Simulates:
  • Worker movement & behaviour on factory floor
  • Edge camera AI inference (PPE detection, posture, zone intrusion)
  • Environmental IoT sensors (gas, temp, humidity, noise, vibration, dust)
  • Edge-node compute metrics (GPU usage, inference latency, FPS, power)
  • Cloud aggregation pipeline metrics
"""

import math
import random
import time
import threading
from datetime import datetime
from config import (
    FLOOR_WIDTH, FLOOR_HEIGHT, ZONES, EDGE_CAMERAS, WORKERS,
    PPE_ITEMS, SENSOR_THRESHOLDS, EDGE_NODE_SPECS, CLOUD_SPECS,
)

# ─────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def point_in_rect(px, py, rx, ry, rw, rh):
    return rx <= px <= rx + rw and ry <= py <= ry + rh

def dist(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def timestamp():
    return datetime.now().strftime("%H:%M:%S")


# ─────────────────────────────────────────────────────────
# Worker Simulation
# ─────────────────────────────────────────────────────────
class WorkerSim:
    """Simulates a single worker moving on the factory floor."""

    def __init__(self, cfg):
        self.id = cfg["id"]
        self.name = cfg["name"]
        self.role = cfg["role"]
        self.shift = cfg["shift"]

        # Position & movement
        self.x = random.randint(100, FLOOR_WIDTH - 100)
        self.y = random.randint(100, FLOOR_HEIGHT - 100)
        self.target_x = self.x
        self.target_y = self.y
        self.speed = random.uniform(1.5, 3.5)

        # PPE status (True = wearing)
        self.ppe = {item: True for item in PPE_ITEMS}
        # Randomly remove one PPE to create violations
        if random.random() < 0.25:
            missing = random.choice(PPE_ITEMS)
            self.ppe[missing] = False

        # Vitals
        self.heart_rate = random.randint(65, 85)
        self.body_temp = round(random.uniform(36.2, 37.0), 1)
        self.fatigue_score = round(random.uniform(0.0, 0.3), 2)
        self.posture_ok = True
        self.is_active = True
        self.current_zone = None

        # Behaviour state
        self._idle_timer = 0
        self._pick_new_target()

    def _pick_new_target(self):
        # Workers tend to move towards zones relevant to their role
        if random.random() < 0.6:
            zone = random.choice(ZONES)
            self.target_x = zone["x"] + random.randint(20, zone["w"] - 20)
            self.target_y = zone["y"] + random.randint(20, zone["h"] - 20)
        else:
            self.target_x = random.randint(40, FLOOR_WIDTH - 40)
            self.target_y = random.randint(40, FLOOR_HEIGHT - 40)
        self._idle_timer = 0

    def update(self):
        # Move towards target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        d = math.sqrt(dx * dx + dy * dy)

        if d < 5:
            self._idle_timer += 1
            if self._idle_timer > random.randint(5, 20):
                self._pick_new_target()
        else:
            self.x += (dx / d) * self.speed
            self.y += (dy / d) * self.speed
            self.x = clamp(self.x, 10, FLOOR_WIDTH - 10)
            self.y = clamp(self.y, 10, FLOOR_HEIGHT - 10)

        # Update vitals with realistic drift
        self.heart_rate = clamp(self.heart_rate + random.randint(-2, 2), 55, 130)
        self.body_temp = round(clamp(self.body_temp + random.uniform(-0.05, 0.05), 35.8, 38.5), 1)

        # Fatigue increases slowly over time
        self.fatigue_score = round(clamp(
            self.fatigue_score + random.uniform(-0.01, 0.02), 0.0, 1.0
        ), 2)

        # Random posture change
        if random.random() < 0.03:
            self.posture_ok = not self.posture_ok
        if random.random() < 0.06:
            self.posture_ok = True

        # Random PPE changes (simulates workers removing/wearing PPE)
        if random.random() < 0.008:
            item = random.choice(PPE_ITEMS)
            self.ppe[item] = not self.ppe[item]

        # Determine current zone
        self.current_zone = None
        for zone in ZONES:
            if point_in_rect(self.x, self.y, zone["x"], zone["y"], zone["w"], zone["h"]):
                self.current_zone = zone["id"]
                break

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "shift": self.shift,
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "ppe": dict(self.ppe),
            "ppe_compliance": all(self.ppe.values()),
            "heart_rate": self.heart_rate,
            "body_temp": self.body_temp,
            "fatigue_score": self.fatigue_score,
            "posture_ok": self.posture_ok,
            "is_active": self.is_active,
            "current_zone": self.current_zone,
        }


# ─────────────────────────────────────────────────────────
# Environmental Sensor Simulation
# ─────────────────────────────────────────────────────────
class EnvironmentSensorSim:
    """Simulates all environmental IoT sensors for a zone."""

    def __init__(self, zone_id):
        self.zone_id = zone_id
        self.readings = {}
        self._init_readings()

    def _init_readings(self):
        for sensor, spec in SENSOR_THRESHOLDS.items():
            nominal = (spec["warn"] + spec["min"]) / 2
            self.readings[sensor] = round(nominal + random.uniform(-2, 2), 1)

    def update(self):
        for sensor, spec in SENSOR_THRESHOLDS.items():
            # Drift with mean reversion
            current = self.readings[sensor]
            nominal = (spec["warn"] + spec["min"]) / 2
            drift = random.gauss(0, 0.5) + (nominal - current) * 0.02

            # Occasional spikes
            if random.random() < 0.015:
                drift += random.uniform(3, 8) * random.choice([-1, 1])

            self.readings[sensor] = round(
                clamp(current + drift, spec["min"], spec["max"]), 1
            )

    def get_status(self, sensor):
        """Returns 'normal', 'warning', or 'critical'."""
        val = self.readings[sensor]
        spec = SENSOR_THRESHOLDS[sensor]
        if val >= spec["critical"]:
            return "critical"
        elif val >= spec["warn"]:
            return "warning"
        return "normal"

    def to_dict(self):
        data = {}
        for sensor in SENSOR_THRESHOLDS:
            data[sensor] = {
                "value": self.readings[sensor],
                "unit": SENSOR_THRESHOLDS[sensor]["unit"],
                "status": self.get_status(sensor),
                "threshold_warn": SENSOR_THRESHOLDS[sensor]["warn"],
                "threshold_critical": SENSOR_THRESHOLDS[sensor]["critical"],
            }
        return {"zone_id": self.zone_id, "sensors": data}


# ─────────────────────────────────────────────────────────
# Edge Camera AI Simulation
# ─────────────────────────────────────────────────────────
class EdgeCameraSim:
    """Simulates an edge camera with on-device AI inference."""

    def __init__(self, cfg):
        self.id = cfg["id"]
        self.name = cfg["name"]
        self.x = cfg["x"]
        self.y = cfg["y"]
        self.fov_radius = cfg["fov_radius"]
        self.zone = cfg["zone"]

        # Edge compute metrics
        self.fps = random.uniform(22, 28)
        self.inference_ms = random.uniform(*EDGE_NODE_SPECS["inference_time_ms_range"])
        self.gpu_utilization = random.uniform(45, 65)
        self.cpu_utilization = random.uniform(30, 50)
        self.ram_usage_pct = random.uniform(50, 70)
        self.power_watts = random.uniform(*EDGE_NODE_SPECS["power_watts_range"])
        self.temperature_c = random.uniform(45, 60)
        self.detections = []
        self.is_online = True
        self.uptime_s = 0

    def detect_workers(self, workers):
        """Simulate AI detection of workers in camera FOV."""
        self.detections = []
        for w in workers:
            if dist(self.x, self.y, w.x, w.y) <= self.fov_radius:
                confidence = round(random.uniform(0.82, 0.99), 2)
                self.detections.append({
                    "worker_id": w.id,
                    "worker_name": w.name,
                    "confidence": confidence,
                    "bbox": {
                        "x": int(w.x - 15),
                        "y": int(w.y - 25),
                        "w": 30,
                        "h": 50,
                    },
                    "ppe_detected": dict(w.ppe),
                    "posture_ok": w.posture_ok,
                    "fatigue_flag": w.fatigue_score > 0.7,
                })

    def update_metrics(self):
        """Update edge node compute metrics."""
        self.fps = round(clamp(self.fps + random.uniform(-1.5, 1.5), 15, 30), 1)
        self.inference_ms = round(clamp(
            self.inference_ms + random.uniform(-3, 3),
            *EDGE_NODE_SPECS["inference_time_ms_range"]
        ), 1)
        self.gpu_utilization = round(clamp(
            self.gpu_utilization + random.uniform(-5, 5), 20, 98
        ), 1)
        self.cpu_utilization = round(clamp(
            self.cpu_utilization + random.uniform(-4, 4), 10, 95
        ), 1)
        self.ram_usage_pct = round(clamp(
            self.ram_usage_pct + random.uniform(-2, 2), 40, 95
        ), 1)
        self.power_watts = round(clamp(
            self.power_watts + random.uniform(-0.5, 0.5),
            *EDGE_NODE_SPECS["power_watts_range"]
        ), 1)
        self.temperature_c = round(clamp(
            self.temperature_c + random.uniform(-1, 1), 38, 78
        ), 1)
        self.uptime_s += 1

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "fov_radius": self.fov_radius,
            "zone": self.zone,
            "fps": self.fps,
            "inference_ms": self.inference_ms,
            "gpu_util": self.gpu_utilization,
            "cpu_util": self.cpu_utilization,
            "ram_pct": self.ram_usage_pct,
            "power_w": self.power_watts,
            "temp_c": self.temperature_c,
            "is_online": self.is_online,
            "uptime_s": self.uptime_s,
            "detections": self.detections,
            "detection_count": len(self.detections),
        }


# ─────────────────────────────────────────────────────────
# Alert Manager
# ─────────────────────────────────────────────────────────
class AlertManager:
    """Generates and manages safety alerts."""

    def __init__(self):
        self.alerts = []
        self.alert_id_counter = 0
        self.max_alerts = 100

    def add(self, level, category, message, source="system"):
        self.alert_id_counter += 1
        alert = {
            "id": self.alert_id_counter,
            "timestamp": timestamp(),
            "level": level,
            "category": category,
            "message": message,
            "source": source,
            "acknowledged": False,
        }
        self.alerts.insert(0, alert)
        if len(self.alerts) > self.max_alerts:
            self.alerts.pop()
        return alert

    def acknowledge(self, alert_id):
        for a in self.alerts:
            if a["id"] == alert_id:
                a["acknowledged"] = True
                return True
        return False

    def clear_all(self):
        self.alerts.clear()

    def get_recent(self, n=20):
        return self.alerts[:n]

    def get_stats(self):
        total = len(self.alerts)
        by_level = {}
        for a in self.alerts:
            by_level[a["level"]] = by_level.get(a["level"], 0) + 1
        return {"total": total, "by_level": by_level}


# ─────────────────────────────────────────────────────────
# Cloud Pipeline Simulation
# ─────────────────────────────────────────────────────────
class CloudPipelineSim:
    """Simulates cloud aggregation metrics."""

    def __init__(self):
        self.latency_ms = random.uniform(*CLOUD_SPECS["latency_ms_range"])
        self.bandwidth_used_mbps = random.uniform(10, 40)
        self.packets_sent = 0
        self.packets_dropped = 0
        self.edge_to_cloud_sync = True
        self.mqtt_connected = True
        self.data_points_processed = 0
        self.ai_model_accuracy = round(random.uniform(0.92, 0.97), 3)
        self.cloud_cpu = random.uniform(20, 40)
        self.cloud_ram = random.uniform(35, 55)

    def update(self):
        self.latency_ms = round(clamp(
            self.latency_ms + random.uniform(-10, 10),
            *CLOUD_SPECS["latency_ms_range"]
        ), 1)
        self.bandwidth_used_mbps = round(clamp(
            self.bandwidth_used_mbps + random.uniform(-3, 3), 5, 90
        ), 1)
        self.packets_sent += random.randint(10, 30)
        if random.random() < 0.03:
            self.packets_dropped += 1
        self.data_points_processed += random.randint(50, 200)
        self.ai_model_accuracy = round(clamp(
            self.ai_model_accuracy + random.uniform(-0.002, 0.002), 0.88, 0.99
        ), 3)
        self.cloud_cpu = round(clamp(self.cloud_cpu + random.uniform(-3, 3), 10, 85), 1)
        self.cloud_ram = round(clamp(self.cloud_ram + random.uniform(-2, 2), 25, 80), 1)

        # Occasional sync issues
        if random.random() < 0.02:
            self.edge_to_cloud_sync = False
        elif random.random() < 0.1:
            self.edge_to_cloud_sync = True

    def to_dict(self):
        return {
            "latency_ms": self.latency_ms,
            "bandwidth_mbps": self.bandwidth_used_mbps,
            "packets_sent": self.packets_sent,
            "packets_dropped": self.packets_dropped,
            "packet_loss_pct": round(
                (self.packets_dropped / max(self.packets_sent, 1)) * 100, 2
            ),
            "sync_status": self.edge_to_cloud_sync,
            "mqtt_connected": self.mqtt_connected,
            "data_points": self.data_points_processed,
            "model_accuracy": self.ai_model_accuracy,
            "cloud_cpu": self.cloud_cpu,
            "cloud_ram": self.cloud_ram,
            "provider": CLOUD_SPECS["provider"],
            "region": CLOUD_SPECS["region"],
        }


# ─────────────────────────────────────────────────────────
# Main Simulation Engine
# ─────────────────────────────────────────────────────────
class SimulationEngine:
    """
    Orchestrates all simulation components.
    Call .tick() periodically to advance the simulation.
    """

    def __init__(self):
        self.workers = [WorkerSim(w) for w in WORKERS]
        self.cameras = [EdgeCameraSim(c) for c in EDGE_CAMERAS]
        self.env_sensors = {z["id"]: EnvironmentSensorSim(z["id"]) for z in ZONES}
        self.cloud = CloudPipelineSim()
        self.alerts = AlertManager()
        self.tick_count = 0
        self.start_time = time.time()
        self._last_alert_check = 0

    def tick(self):
        """Advance all simulations by one step."""
        self.tick_count += 1

        # Update workers
        for w in self.workers:
            w.update()

        # Update cameras & detections
        for cam in self.cameras:
            cam.detect_workers(self.workers)
            cam.update_metrics()

        # Update environment sensors
        for sensor in self.env_sensors.values():
            sensor.update()

        # Update cloud pipeline
        self.cloud.update()

        # Check for alerts every 3 ticks
        if self.tick_count - self._last_alert_check >= 3:
            self._check_alerts()
            self._last_alert_check = self.tick_count

    def _check_alerts(self):
        """Analyse simulation state and generate alerts."""

        # PPE violations
        for w in self.workers:
            missing_ppe = [item for item, worn in w.ppe.items() if not worn]
            if missing_ppe and w.current_zone:
                zone_cfg = next((z for z in ZONES if z["id"] == w.current_zone), None)
                if zone_cfg:
                    required = zone_cfg.get("required_ppe", [])
                    violations = [p for p in missing_ppe if p in required]
                    if violations:
                        self.alerts.add(
                            "high", "PPE Violation",
                            f"{w.name} missing {', '.join(violations)} in {zone_cfg['name']}",
                            source=w.id
                        )

            # Fatigue alert
            if w.fatigue_score > 0.75:
                self.alerts.add(
                    "high", "Fatigue",
                    f"{w.name} fatigue score {w.fatigue_score} — rest recommended",
                    source=w.id
                )

            # Posture alert
            if not w.posture_ok:
                self.alerts.add(
                    "medium", "Posture",
                    f"{w.name} poor posture detected — ergonomic risk",
                    source=w.id
                )

            # Heart rate alert
            if w.heart_rate > 110:
                self.alerts.add(
                    "high", "Vital Sign",
                    f"{w.name} elevated heart rate: {w.heart_rate} bpm",
                    source=w.id
                )

        # Zone overcrowding
        for zone_cfg in ZONES:
            zid = zone_cfg["id"]
            count = sum(1 for w in self.workers if w.current_zone == zid)
            if count > zone_cfg["max_workers"]:
                self.alerts.add(
                    "critical", "Zone Overcrowding",
                    f"{zone_cfg['name']} has {count}/{zone_cfg['max_workers']} workers — overcrowded!",
                    source=zid
                )

        # Environment hazards
        for zid, env in self.env_sensors.items():
            for sensor in SENSOR_THRESHOLDS:
                status = env.get_status(sensor)
                zone_name = next((z["name"] for z in ZONES if z["id"] == zid), zid)
                if status == "critical":
                    self.alerts.add(
                        "critical", "Environment",
                        f"{zone_name}: {sensor} at {env.readings[sensor]} "
                        f"{SENSOR_THRESHOLDS[sensor]['unit']} — CRITICAL!",
                        source=zid
                    )
                elif status == "warning":
                    self.alerts.add(
                        "medium", "Environment",
                        f"{zone_name}: {sensor} at {env.readings[sensor]} "
                        f"{SENSOR_THRESHOLDS[sensor]['unit']} — warning",
                        source=zid
                    )

        # Camera offline simulation
        for cam in self.cameras:
            if random.random() < 0.005:
                cam.is_online = False
                self.alerts.add(
                    "high", "Edge Node",
                    f"{cam.name} went offline!",
                    source=cam.id
                )
            elif not cam.is_online and random.random() < 0.1:
                cam.is_online = True
                self.alerts.add(
                    "info", "Edge Node",
                    f"{cam.name} back online",
                    source=cam.id
                )

    # ── Data accessors ───────────────────────────────────
    def get_full_state(self):
        """Return complete simulation state for initial load."""
        return {
            "workers": [w.to_dict() for w in self.workers],
            "cameras": [c.to_dict() for c in self.cameras],
            "env_sensors": {zid: s.to_dict() for zid, s in self.env_sensors.items()},
            "cloud": self.cloud.to_dict(),
            "alerts": self.alerts.get_recent(30),
            "alert_stats": self.alerts.get_stats(),
            "zones": ZONES,
            "floor": {"width": FLOOR_WIDTH, "height": FLOOR_HEIGHT},
            "uptime": int(time.time() - self.start_time),
            "tick": self.tick_count,
            "edge_specs": EDGE_NODE_SPECS,
            "cloud_specs": CLOUD_SPECS,
        }

    def get_realtime_update(self):
        """Return lightweight update for real-time streaming."""
        return {
            "workers": [w.to_dict() for w in self.workers],
            "cameras": [c.to_dict() for c in self.cameras],
            "env_sensors": {zid: s.to_dict() for zid, s in self.env_sensors.items()},
            "cloud": self.cloud.to_dict(),
            "alerts": self.alerts.get_recent(10),
            "alert_stats": self.alerts.get_stats(),
            "uptime": int(time.time() - self.start_time),
            "tick": self.tick_count,
        }

    def trigger_incident(self, incident_type):
        """Manually trigger a simulated incident for demo purposes."""
        if incident_type == "gas_leak":
            zone = random.choice(list(self.env_sensors.values()))
            zone.readings["gas_co"] = random.uniform(60, 95)
            zone.readings["gas_h2s"] = random.uniform(25, 45)
            self.alerts.add("critical", "Gas Leak",
                            "Toxic gas leak detected! Evacuate immediately!", source="system")
        elif incident_type == "fire":
            zone = random.choice(list(self.env_sensors.values()))
            zone.readings["temperature"] = random.uniform(60, 80)
            self.alerts.add("critical", "Fire",
                            "Fire detected! Emergency protocol activated!", source="system")
        elif incident_type == "worker_fall":
            worker = random.choice(self.workers)
            worker.posture_ok = False
            worker.fatigue_score = 0.95
            worker.heart_rate = 130
            self.alerts.add("critical", "Worker Down",
                            f"{worker.name} potential fall detected — immediate response needed!",
                            source=worker.id)
        elif incident_type == "intrusion":
            worker = random.choice(self.workers)
            zone = next((z for z in ZONES if z["type"] == "restricted"), ZONES[1])
            worker.x = zone["x"] + zone["w"] // 2
            worker.y = zone["y"] + zone["h"] // 2
            worker.target_x = worker.x
            worker.target_y = worker.y
            self.alerts.add("critical", "Zone Intrusion",
                            f"Unauthorized: {worker.name} entered {zone['name']}!",
                            source=worker.id)
        elif incident_type == "ppe_mass":
            for w in self.workers:
                w.ppe["helmet"] = False
                w.ppe["vest"] = False
            self.alerts.add("high", "PPE Alert",
                            "Multiple workers detected without required PPE!", source="system")
        return True
