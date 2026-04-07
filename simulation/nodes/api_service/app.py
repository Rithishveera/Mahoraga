import os
from flask import Flask, request, jsonify

app = Flask(__name__)

IS_PATCHED: dict[str, bool] = {
    "injection": False,
    "weak_creds": False,
    "unprotected": False,
}

VALID_CREDS: dict[str, str] = {
    "admin": "admin",
    "user": "password",
    "root": "root",
}

NODE_NAME = os.getenv("NODE_NAME", "api_service")
PORT = int(os.getenv("PORT", 5002))


@app.route("/health")
def health() -> tuple:
    return jsonify({"status": "ok", "node": NODE_NAME, "patched": IS_PATCHED}), 200


@app.route("/users")
def users() -> tuple:
    uid = request.args.get("id", "1")
    if not IS_PATCHED["injection"]:
        return jsonify({
            "query": f"SELECT * FROM users WHERE id={uid}",
            "data": {"id": uid, "name": "John", "role": "admin"},
        }), 200
    return jsonify({"error": "invalid input"}), 400


@app.route("/login", methods=["POST"])
def login() -> tuple:
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("user", "")
    password = data.get("pass", "")
    if not IS_PATCHED["weak_creds"]:
        if VALID_CREDS.get(username) == password:
            return jsonify({"token": "abc123", "role": "admin", "message": "login success"}), 200
        return jsonify({"error": "invalid credentials"}), 401
    return jsonify({"error": "account locked — contact admin"}), 403


@app.route("/internal")
def internal() -> tuple:
    if not IS_PATCHED["unprotected"]:
        return jsonify({
            "db_host": "localhost",
            "db_pass": "secret123",
            "api_key": "sk-internal-key",
        }), 200
    return jsonify({"error": "403 forbidden"}), 403


@app.route("/state")
def state() -> tuple:
    return jsonify({"node": NODE_NAME, "port": PORT, "patched": IS_PATCHED}), 200


@app.route("/reset")
def reset() -> tuple:
    global IS_PATCHED
    IS_PATCHED = {"injection": False, "weak_creds": False, "unprotected": False}
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
