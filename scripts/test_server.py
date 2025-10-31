#!/usr/bin/env python3


import os, time
from flask import Flask, request, jsonify

from flask import render_template


AUTH_TOKEN = os.getenv("HOST_TOKEN", "HOST_TOKEN_123")


latest_data = {}

app = Flask(__name__)

@app.post("/api/v1/metrics")
def metrics():
    global latest_data
    if request.headers.get("Authorization") != f"Bearer {AUTH_TOKEN}":
        return jsonify({"error":"unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    latest_data = data  # store last received payload
    host = data.get("host")
    mem_pct = data.get("memory",{}).get("mem_pct")
    disks = data.get("disks",[])
    worst = max([d.get("pct_used",0) for d in disks], default=0)
    print(f"[{time.strftime('%H:%M:%S')}] ✅ from {host}  mem={mem_pct}%  max_disk={worst}%")
    return jsonify({"status":"ok"}), 200

@app.get("/latest")
def latest():
    return jsonify(latest_data or {"note": "no data yet"})

@app.get("/healthz")
def healthz():
    return "ok", 200


@app.get("/view")
def view():
    return render_template("view.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
