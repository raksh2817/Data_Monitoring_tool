import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

import pymysql
import yaml
from flask import Flask, request, jsonify
from pydantic import BaseModel, Field, ValidationError, field_validator
from werkzeug.exceptions import BadRequest


def load_config() -> tuple[dict, Path]:
    """
    Locate and load the YAML configuration file. Prefer an explicit
    `APP_CONFIG_PATH` environment variable, then fall back to common
    filenames relative to the project structure.
    """
    candidate_paths = []

    # Highest precedence: explicit environment override
    env_path = os.getenv("APP_CONFIG_PATH")
    if env_path:
        candidate_paths.append(Path(env_path))

    # Next: look alongside this script and one level above (project root)
    script_dir = Path(__file__).resolve().parent
    search_roots = [script_dir, script_dir.parent]
    for root in search_roots:
        candidate_paths.extend(
            [
                root / "config.yaml",
                root / "config.yml",
            ]
        )

    # Remove duplicates while preserving order
    seen = set()
    unique_paths = []
    for path in candidate_paths:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)

    for path in unique_paths:
        if path.is_file():
            with path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f), path

    searched = "\n  ".join(str(p) for p in unique_paths)
    raise FileNotFoundError(
        "Missing config file. Looked in:\n  {}".format(searched)
    )


config, CONFIG_PATH = load_config()

# Validate minimal required keys (defensive)
for sect, keys in {
    "database": ["host", "port", "user", "password", "name", "charset"],
    "auth": ["header", "prefix"],
    "flask": ["host", "port", "debug"],
}.items():
    missing = [k for k in keys if k not in config.get(sect, {})]
    if missing:
        raise RuntimeError(f"Missing keys in config.yml -> {sect}: {missing}")

DB_CFG = dict(
    host=config["database"]["host"],
    port=int(config["database"]["port"]),
    user=config["database"]["user"],
    password=config["database"]["password"],
    database=config["database"]["name"],
    charset=config["database"]["charset"],
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True,
)

AUTH_HEADER = config["auth"]["header"]
AUTH_PREFIX = config["auth"]["prefix"]

# Flask initialization
app = Flask(__name__)

def db():
    return pymysql.connect(**DB_CFG)

# ---------- Pydantic schema for incoming payload ----------
class ReportPayload(BaseModel):
    # auth: prefer header "Authorization: Bearer <host_key>", else accept JSON field
    host_key: Optional[str] = None

    collected_at: Optional[datetime] = None
    int_ip: Optional[str] = None
    public_ip: Optional[str] = None

    # optional kernel/info
    kernel_name: Optional[str] = None
    kernel_version: Optional[str] = None

    # metrics
    cpu_pct: Optional[float] = Field(default=None, ge=0, le=100)
    mem_used_mb: Optional[int] = None
    mem_total_mb: Optional[int] = None
    mem_pct: Optional[float] = Field(default=None, ge=0, le=100)

    disk_used_gb: Optional[float] = None
    disk_total_gb: Optional[float] = None
    disk_pct: Optional[float] = Field(default=None, ge=0, le=100)

    # data-pipeline fields (optional for now)
    dataset_name: Optional[str] = None
    partition_key: Optional[str] = None
    files_count: Optional[int] = None
    size_bytes: Optional[int] = None
    min_event_ts: Optional[datetime] = None
    max_event_ts: Optional[datetime] = None

    # catchall
    extra: Optional[Any] = None

    @field_validator("collected_at", mode="before")
    @classmethod
    def default_collected_at(cls, v):
        return v or datetime.now(timezone.utc)

def get_host_key_from_request():
    # Prefer configured Authorization header/prefix
    auth = request.headers.get(AUTH_HEADER, "")
    if auth.lower().startswith(AUTH_PREFIX.lower()):
        return auth[len(AUTH_PREFIX):].strip()
    # Fallback: JSON field
    try:
        body = request.get_json(silent=True) or {}
        if isinstance(body, dict) and "host_key" in body:
            return body["host_key"]
    except Exception:
        pass
    return None

def get_host_id_by_key(conn, host_key: str) -> Optional[int]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT host_id FROM hosts WHERE host_key=%s AND is_active=1",
            (host_key,),
        )
        row = cur.fetchone()
        return row["host_id"] if row else None

def update_last_seen(conn, host_id: int):
    with conn.cursor() as cur:
        cur.execute("UPDATE hosts SET last_seen=NOW() WHERE host_id=%s", (host_id,))

def insert_incoming_data(conn, host_id: int, p: ReportPayload) -> int:
    cols = [
        "host_id","collected_at","created_at",
        "int_ip","public_ip",
        "kernel_name","kernel_version",
        "cpu_pct","mem_used_mb","mem_total_mb","mem_pct",
        "disk_used_gb","disk_total_gb","disk_pct",
        "dataset_name","partition_key","files_count","size_bytes",
        "min_event_ts","max_event_ts","extra"
    ]
    sql = f"""
        INSERT INTO incoming_data ({",".join(cols)})
        VALUES (%s,%s,NOW(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    vals = (
        host_id,
        p.collected_at.replace(tzinfo=None) if p.collected_at else None,
        p.int_ip, p.public_ip,
        p.kernel_name, p.kernel_version,
        p.cpu_pct, p.mem_used_mb, p.mem_total_mb, p.mem_pct,
        p.disk_used_gb, p.disk_total_gb, p.disk_pct,
        p.dataset_name, p.partition_key, p.files_count, p.size_bytes,
        (p.min_event_ts.replace(tzinfo=None) if p.min_event_ts else None),
        (p.max_event_ts.replace(tzinfo=None) if p.max_event_ts else None),
        json.dumps(p.extra) if p.extra is not None else None,
    )
    with conn.cursor() as cur:
        cur.execute(sql, vals)
        return cur.lastrowid

@app.post("/report")
def report():
    # 1) Auth
    host_key = get_host_key_from_request()
    if not host_key:
        return jsonify({"ok": False, "error": "missing_host_key"}), 401

    # 2) Parse + validate JSON
    try:
        body = request.get_json(force=True)
    except BadRequest:
        return jsonify({"ok": False, "error": "invalid_json"}), 400

    try:
        payload = ReportPayload.model_validate(body)
    except ValidationError as ve:
        return jsonify({"ok": False, "error": "validation_error", "details": ve.errors()}), 400

    # Ensure body host_key (if present) matches header
    if payload.host_key and payload.host_key != host_key:
        return jsonify({"ok": False, "error": "host_key_mismatch"}), 401

    # 3) DB ops
    conn = None
    try:
        conn = db()
        host_id = get_host_id_by_key(conn, host_key)
        if not host_id:
            return jsonify({"ok": False, "error": "invalid_host_key"}), 403

        data_id = insert_incoming_data(conn, host_id, payload)
        update_last_seen(conn, host_id)

        return jsonify({"ok": True, "data_id": data_id}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": "server_error", "details": str(e)}), 500
    finally:
        try:
            if conn: conn.close()
        except Exception:
            pass

@app.get("/health")
def health():
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("SELECT 1 as ok")
            cur.fetchone()
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(
        host=config["flask"].get("host", "0.0.0.0"),
        port=int(config["flask"].get("port", 5000)),
        debug=bool(config["flask"].get("debug", False)),
    )

