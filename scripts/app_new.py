import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

import pymysql
import yaml
from flask import Flask, request, jsonify, redirect, url_for, flash
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
app.secret_key = secrets.token_hex(16)  # For flash messages

def db():
    return pymysql.connect(**DB_CFG)

# Main entry point moved to bottom of file

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
    # DEBUG - Add these lines
    print(f"\n{'='*60}")
    print(f"Incoming request from {request.remote_addr}")
    print(f"Authorization header: {request.headers.get('Authorization', 'NONE')}")
    try:
        print(f"Body keys: {list(request.get_json(force=True).keys())}")
    except:
        pass
    print(f"{'='*60}\n")
    # END DEBUG
    
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

from flask import render_template
from datetime import datetime

@app.route('/')
@app.route('/dashboard')
def dashboard():
    conn = db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT h.host_id, h.host_name, h.os_name, h.os_version, h.last_seen,
                    CASE 
                        WHEN h.last_seen > DATE_SUB(NOW(), INTERVAL 5 MINUTE) THEN 'online'
                        WHEN h.last_seen > DATE_SUB(NOW(), INTERVAL 60 MINUTE) THEN 'warning'
                        ELSE 'offline'
                    END as status,
                    (SELECT COUNT(*) FROM alerts a WHERE a.host_id = h.host_id AND a.status = 'open') as alert_count,
                    (SELECT cpu_pct FROM incoming_data WHERE host_id = h.host_id ORDER BY collected_at DESC LIMIT 1) as cpu_pct,
                    (SELECT mem_pct FROM incoming_data WHERE host_id = h.host_id ORDER BY collected_at DESC LIMIT 1) as mem_pct,
                    (SELECT disk_pct FROM incoming_data WHERE host_id = h.host_id ORDER BY collected_at DESC LIMIT 1) as disk_pct,
                    (SELECT collected_at FROM incoming_data WHERE host_id = h.host_id ORDER BY collected_at DESC LIMIT 1) as metrics_time
                FROM hosts h
                WHERE h.is_active = 1
                ORDER BY h.host_name
            """)
            hosts = cur.fetchall()
            cur.execute("SELECT COUNT(*) as total FROM hosts WHERE is_active = 1")
            total_hosts = cur.fetchone()['total']
            cur.execute("SELECT COUNT(*) as total FROM hosts WHERE is_active = 1 AND last_seen > DATE_SUB(NOW(), INTERVAL 5 MINUTE)")
            online_hosts = cur.fetchone()['total']
            cur.execute("SELECT COUNT(*) as total FROM alerts WHERE status = 'open'")
            active_alerts = cur.fetchone()['total']
        conn.close()
        return render_template('dashboard.html', hosts=hosts, total_hosts=total_hosts, 
                             online_hosts=online_hosts, active_alerts=active_alerts, 
                             current_time=datetime.now())
    except Exception as e:
        conn.close()
        return f"Error: {e}", 500

@app.route('/alerts')
def alerts_page():
    conn = db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.alert_id, a.host_id, h.host_name, at.check_name, a.severity, 
                       a.status, a.message, a.triggered_at,
                       TIMESTAMPDIFF(MINUTE, a.triggered_at, NOW()) as minutes_ago
                FROM alerts a
                JOIN hosts h ON a.host_id = h.host_id
                JOIN alert_types at ON a.check_id = at.check_id
                ORDER BY CASE a.status WHEN 'open' THEN 1 WHEN 'acknowledged' THEN 2 ELSE 3 END,
                         a.triggered_at DESC
                LIMIT 100
            """)
            alerts = cur.fetchall()
            cur.execute("SELECT status, COUNT(*) as count FROM alerts GROUP BY status")
            stats = {row['status']: row['count'] for row in cur.fetchall()}
        conn.close()
        return render_template('alerts.html', alerts=alerts, stats=stats, current_time=datetime.now())
    except Exception as e:
        conn.close()
        return f"Error: {e}", 500

@app.route('/host/<int:host_id>')
def host_details(host_id):
    conn = db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT host_id, host_name, os_name, os_version, last_seen, created_at,
                    CASE 
                        WHEN last_seen > DATE_SUB(NOW(), INTERVAL 5 MINUTE) THEN 'online'
                        WHEN last_seen > DATE_SUB(NOW(), INTERVAL 60 MINUTE) THEN 'warning'
                        ELSE 'offline'
                    END as status
                FROM hosts WHERE host_id = %s
            """, (host_id,))
            host = cur.fetchone()
            if not host:
                return "Host not found", 404
            cur.execute("""
                SELECT collected_at, cpu_pct, mem_pct, disk_pct, mem_used_mb, mem_total_mb,
                       disk_used_gb, disk_total_gb
                FROM incoming_data
                WHERE host_id = %s AND collected_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                ORDER BY collected_at DESC LIMIT 100
            """, (host_id,))
            metrics = cur.fetchall()
            cur.execute("""
                SELECT a.alert_id, at.check_name, a.severity, a.status, a.message, a.triggered_at,
                       TIMESTAMPDIFF(MINUTE, a.triggered_at, NOW()) as minutes_ago
                FROM alerts a
                JOIN alert_types at ON a.check_id = at.check_id
                WHERE a.host_id = %s
                ORDER BY a.triggered_at DESC LIMIT 20
            """, (host_id,))
            alerts = cur.fetchall()
        conn.close()
        return render_template('host_details.html', host=host, metrics=metrics, 
                             alerts=alerts, current_time=datetime.now())
    except Exception as e:
        conn.close()
        return f"Error: {e}", 500

@app.route('/add-host', methods=['GET', 'POST'])
def add_host():
    """Add a new host to the monitoring system"""
    if request.method == 'GET':
        return render_template('add_host.html', current_time=datetime.now())
    
    # Handle POST request
    host_name = request.form.get('host_name', '').strip()
    os_name = request.form.get('os_name', '').strip()
    os_version = request.form.get('os_version', '').strip()
    host_key = request.form.get('host_key', '').strip()
    generate_key = request.form.get('generate_key') == 'on'
    
    # Validation
    errors = []
    if not host_name:
        errors.append("Host name is required")
    if len(host_name) > 255:
        errors.append("Host name must be 255 characters or less")
    
    # Generate or validate host key
    if generate_key:
        host_key = secrets.token_urlsafe(32)
    elif not host_key:
        errors.append("Host key is required (or check 'Generate Key')")
    elif len(host_key) > 64:
        errors.append("Host key must be 64 characters or less")
    
    if errors:
        return render_template('add_host.html', 
                             errors=errors,
                             host_name=host_name,
                             os_name=os_name,
                             os_version=os_version,
                             host_key=host_key if not generate_key else '',
                             current_time=datetime.now())
    
    # Insert into database
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            # Check if host_name already exists
            cur.execute("SELECT host_id FROM hosts WHERE host_name = %s", (host_name,))
            if cur.fetchone():
                errors.append(f"Host name '{host_name}' already exists")
                return render_template('add_host.html',
                                     errors=errors,
                                     host_name=host_name,
                                     os_name=os_name,
                                     os_version=os_version,
                                     host_key=host_key,
                                     current_time=datetime.now())
            
            # Check if host_key already exists
            cur.execute("SELECT host_id FROM hosts WHERE host_key = %s", (host_key,))
            if cur.fetchone():
                errors.append(f"Host key already exists. Please use a different key or generate a new one.")
                return render_template('add_host.html',
                                     errors=errors,
                                     host_name=host_name,
                                     os_name=os_name,
                                     os_version=os_version,
                                     host_key='',
                                     current_time=datetime.now())
            
            # Insert new host
            cur.execute("""
                INSERT INTO hosts (host_name, host_key, os_name, os_version, is_active, last_seen, created_at)
                VALUES (%s, %s, %s, %s, 1, NOW(), NOW())
            """, (host_name, host_key, os_name or None, os_version or None))
            
            host_id = cur.lastrowid
            conn.commit()
        
        conn.close()
        
        # Success - redirect to dashboard with message
        flash(f'Host "{host_name}" added successfully! Host Key: {host_key}', 'success')
        return redirect(url_for('dashboard'))
        
    except pymysql.err.IntegrityError as e:
        conn.close()
        if 'uq_host_name' in str(e):
            errors.append(f"Host name '{host_name}' already exists")
        elif 'uq_host_key' in str(e):
            errors.append(f"Host key already exists. Please use a different key or generate a new one.")
        else:
            errors.append(f"Database error: {str(e)}")
        return render_template('add_host.html',
                             errors=errors,
                             host_name=host_name,
                             os_name=os_name,
                             os_version=os_version,
                             host_key=host_key if not generate_key else '',
                             current_time=datetime.now())
    except Exception as e:
        if conn:
            conn.close()
        return render_template('add_host.html',
                             errors=[f"Error adding host: {str(e)}"],
                             host_name=host_name,
                             os_name=os_name,
                             os_version=os_version,
                             host_key=host_key if not generate_key else '',
                             current_time=datetime.now())



if __name__ == '__main__':
    import socket
    import sys
    
    host = config["flask"].get("host", "0.0.0.0")
    port = int(config["flask"].get("port", 5000))
    debug = bool(config["flask"].get("debug", False))
    
    print("\nSystem Information:")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    print("\nNetwork Information:")
    try:
        # Get all possible IP addresses
        hostname = socket.gethostname()
        ips = socket.gethostbyname_ex(hostname)[2]
        print(f"Hostname: {hostname}")
        print("IP Addresses:")
        for ip in ips:
            print(f"  - {ip}")
    except Exception as e:
        print(f"Error getting IP addresses: {e}")
    
    print(f"\nStarting Flask server on {host}:{port}")
    print("\nServer will be accessible at:")
    print(f"  http://localhost:{port}")
    print(f"  http://127.0.0.1:{port}")
    for ip in ips:
        print(f"  http://{ip}:{port}")
    
    # Add CORS headers to allow connections from any source
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except Exception as e:
        print(f"\nError starting Flask server: {e}")
        sys.exit(1)

