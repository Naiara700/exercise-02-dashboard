"""
Exercise 02 — Streamlit Dashboard

Implement a Streamlit frontend that consumes the Node Registry API.

The dashboard must:
- Display a table of all registered nodes (GET /api/nodes from the API)
- Show a form to register a new node (POST /api/nodes)
- Allow deleting a node by name (DELETE /api/nodes/{name})
- Show a health status indicator (GET /health)

The API runs at the URL in the API_URL environment variable (default: http://api:8080).
"""

# TODO: Implement your Streamlit dashboard here

import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for

API_URL = os.getenv("API_URL", "http://api:8080")
TIMEOUT = 5

app = Flask(__name__)

LAYOUT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Node Registry Dashboard</title>
    <style>
        body {
            font-family: sans-serif;
            max-width: 1000px;
            margin: 40px auto;
            padding: 0 20px;
            background: #f5f5f5;
            color: #333;
        }
        h1 { font-size: 1.6rem; margin-bottom: 4px; }
        h2 { font-size: 1.1rem; margin: 28px 0 12px; color: #444; }
        p  { margin: 4px 0; font-size: .9rem; color: #555; }

        .stats {
            display: flex;
            gap: 12px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .stat {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 12px 18px;
            font-size: .85rem;
            min-width: 160px;
        }
        .stat strong { display: block; font-size: .7rem; color: #888; text-transform: uppercase; margin-bottom: 4px; }

        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: .78rem;
            font-weight: 600;
        }
        .badge-ok      { background: #e6f4ea; color: #2e7d32; }
        .badge-error   { background: #fdecea; color: #c62828; }
        .badge-unknown { background: #f0f0f0; color: #777; }
        .badge-active  { background: #e6f4ea; color: #2e7d32; }
        .badge-inactive{ background: #fdecea; color: #c62828; }

        form { display: flex; gap: 8px; flex-wrap: wrap; align-items: flex-end; }
        label { display: flex; flex-direction: column; font-size: .8rem; color: #666; gap: 4px; }
        input {
            padding: 7px 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: .85rem;
            width: 160px;
        }
        input[type=number] { width: 80px; }
        button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            font-size: .85rem;
            cursor: pointer;
            align-self: flex-end;
        }
        .btn-primary { background: #1a73e8; color: #fff; }
        .btn-primary:hover { background: #1558b0; }
        .btn-danger  { background: #d93025; color: #fff; }
        .btn-danger:hover  { background: #a50e0e; }

        table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #ddd; border-radius: 6px; overflow: hidden; }
        th { background: #f0f0f0; padding: 10px 14px; text-align: left; font-size: .78rem; color: #555; text-transform: uppercase; }
        td { padding: 10px 14px; font-size: .85rem; border-top: 1px solid #eee; }
        tr:hover td { background: #fafafa; }

        .notice {
            padding: 10px 14px;
            border-radius: 4px;
            font-size: .85rem;
            margin: 16px 0;
            border-left: 3px solid #1a73e8;
            background: #e8f0fe;
            color: #1a3a6e;
        }
        .notice.error  { border-left-color: #d93025; background: #fdecea; color: #6b1a16; }
        .notice.success{ border-left-color: #2e7d32; background: #e6f4ea; color: #1b4d1e; }
    </style>
</head>
<body>

<h1>Node Registry Dashboard</h1>
<p>UNLu 2026 — Distributed Systems</p>

{% if msg %}
<div class="notice {% if 'error' in msg.lower() %}error{% elif 'registered' in msg or 'deleted' in msg %}success{% endif %}">
    {{ msg }}
</div>
{% endif %}

<div class="stats">
    <div class="stat">
        <strong>API Status</strong>
        {% if health.status == 'ok' %}
            <span class="badge badge-ok">ok</span>
        {% elif health.status == 'offline' %}
            <span class="badge badge-error">offline</span>
        {% else %}
            <span class="badge badge-unknown">{{ health.status }}</span>
        {% endif %}
    </div>
    <div class="stat">
        <strong>Database</strong>
        {% if health.db == 'connected' or health.db == 'ok' %}
            <span class="badge badge-ok">connected</span>
        {% elif health.db == 'unknown' %}
            <span class="badge badge-unknown">unknown</span>
        {% else %}
            <span class="badge badge-error">{{ health.db }}</span>
        {% endif %}
    </div>
    <div class="stat">
        <strong>Active Nodes</strong>
        {{ health.nodes_count }}
    </div>
</div>

<h2>Register a New Node</h2>
<form action="/register" method="POST">
    <label>Name <input type="text" name="name" placeholder="worker-01" required></label>
    <label>Host <input type="text" name="host" placeholder="192.168.1.10" required></label>
    <label>Port <input type="number" name="port" value="8080" min="1" max="65535" required></label>
    <button type="submit" class="btn-primary">Register</button>
</form>

<h2>Registered Nodes</h2>
{% if nodes %}
<table>
    <thead>
        <tr><th>ID</th><th>Name</th><th>Host</th><th>Port</th><th>Status</th><th>Created At</th></tr>
    </thead>
    <tbody>
    {% for node in nodes %}
        <tr>
            <td>{{ node.id }}</td>
            <td>{{ node.name }}</td>
            <td>{{ node.host }}</td>
            <td>{{ node.port }}</td>
            <td>
                {% if node.status == 'active' %}
                    <span class="badge badge-active">active</span>
                {% elif node.status == 'inactive' %}
                    <span class="badge badge-inactive">inactive</span>
                {% else %}
                    <span class="badge badge-unknown">{{ node.status }}</span>
                {% endif %}
            </td>
            <td>{{ node.created_at }}</td>
        </tr>
    {% endfor %}
    </tbody>
</table>
{% else %}
<p>No nodes registered in the system yet.</p>
{% endif %}

<h2>Delete Node (Soft Delete)</h2>
<form action="/delete" method="POST">
    <label>Name <input type="text" name="name" placeholder="worker-01" required></label>
    <button type="submit" class="btn-danger">Confirm Delete</button>
</form>

</body>
</html>
"""


def get_system_state():
    """Fetch health and node list from the API. Returns safe defaults on failure."""
    health = {"status": "offline", "db": "unknown", "nodes_count": 0}
    nodes = []
    try:
        health_resp = requests.get(f"{API_URL}/health", timeout=TIMEOUT)
        health_resp.raise_for_status()
        health = health_resp.json()
    except requests.RequestException:
        pass
    try:
        nodes_resp = requests.get(f"{API_URL}/api/nodes", timeout=TIMEOUT)
        nodes_resp.raise_for_status()
        nodes = nodes_resp.json()
        if not isinstance(nodes, list):
            nodes = []
    except requests.RequestException:
        pass
    return health, nodes


@app.route("/")
def dashboard():
    health_data, nodes_list = get_system_state()
    message = request.args.get("message", "")
    return render_template_string(LAYOUT, health=health_data, nodes=nodes_list, msg=message)


@app.post("/register")
def register():
    name = request.form.get("name", "").strip()
    host = request.form.get("host", "").strip()
    port_raw = request.form.get("port", "8080").strip()

    if not name or not host or not port_raw:
        return redirect(url_for("dashboard", message="Error: All fields are required."))

    try:
        port = int(port_raw)
        if not (1 <= port <= 65535):
            raise ValueError
    except ValueError:
        return redirect(url_for("dashboard", message="Error: Port must be a number between 1 and 65535."))

    payload = {"name": name, "host": host, "port": port}
    try:
        response = requests.post(f"{API_URL}/api/nodes", json=payload, timeout=TIMEOUT)
        if response.status_code == 201:
            msg = f"registered {name}"
        elif response.status_code == 409:
            msg = f"error: '{name}' already exists"
        elif response.status_code == 422:
            msg = "error: validation failed — check your input values"
        else:
            msg = f"error {response.status_code}"
    except requests.ConnectionError:
        msg = "error: could not reach the API"
    except requests.Timeout:
        msg = "error: API request timed out"

    return redirect(url_for("dashboard", message=msg))


@app.post("/delete")
def delete():
    node_name = request.form.get("name", "").strip()

    if not node_name:
        return redirect(url_for("dashboard", message="error: name is required"))

    try:
        response = requests.delete(f"{API_URL}/api/nodes/{node_name}", timeout=TIMEOUT)
        if response.status_code == 204:
            msg = f"deleted {node_name}"
        elif response.status_code == 404:
            msg = f"error: '{node_name}' not found"
        else:
            msg = f"error {response.status_code}"
    except requests.ConnectionError:
        msg = "error: could not reach the API"
    except requests.Timeout:
        msg = "error: API request timed out"

    return redirect(url_for("dashboard", message=msg))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501)