import os
from flask import Flask, request, jsonify

app = Flask(__name__)

IS_PATCHED: dict[str, bool] = {
    "default_creds": False,
    "user_enum": False,
    "priv_escalation": False,
}

DEFAULT_CREDS: list[dict] = [
    {"user": "root", "pass": "root"},
    {"user": "admin", "pass": "admin"},
    {"user": "superuser", "pass": "password"},
]

NODE_NAME = os.getenv("NODE_NAME", "admin_panel")
PORT = int(os.getenv("PORT", 5004))


@app.route("/health")
def health() -> tuple:
    return jsonify({"status": "ok", "node": NODE_NAME, "patched": IS_PATCHED}), 200


@app.route("/login", methods=["POST"])
def login() -> tuple:
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("user", "")
    password = data.get("pass", "")
    if not IS_PATCHED["default_creds"]:
        for cred in DEFAULT_CREDS:
            if cred["user"] == username and cred["pass"] == password:
                return jsonify({
                    "success": True,
                    "token": "admin-token-xyz",
                    "privileges": "root",
                }), 200
        return jsonify({"success": False}), 401
    return jsonify({"error": "password policy enforced"}), 403


@app.route("/users")
def users() -> tuple:
    if not IS_PATCHED["user_enum"]:
        return jsonify({
            "users": ["root", "admin", "superuser", "john", "alice"],
            "count": 5,
        }), 200
    return jsonify({"error": "403 forbidden"}), 403


@app.route("/escalate")
def escalate() -> tuple:
    if not IS_PATCHED["priv_escalation"]:
        return jsonify({
            "status": "escalated",
            "new_role": "root",
            "message": "privilege escalation successful",
        }), 200
    return jsonify({"error": "access denied"}), 403


@app.route("/state")
def state() -> tuple:
    return jsonify({"node": NODE_NAME, "port": PORT, "patched": IS_PATCHED}), 200


@app.route("/reset")
def reset() -> tuple:
    global IS_PATCHED
    IS_PATCHED = {"default_creds": False, "user_enum": False, "priv_escalation": False}
    return jsonify({"reset": True}), 200


@app.route("/patch", methods=["POST"])
def patch() -> tuple:
    data = request.get_json(force=True, silent=True) or {}
    vuln = data.get("vuln", "")
    if vuln in IS_PATCHED:
        IS_PATCHED[vuln] = True
        return jsonify({"patched": True, "vuln": vuln}), 200
    return jsonify({"error": "unknown vulnerability", "vuln": vuln}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
