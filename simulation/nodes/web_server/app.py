import os
from flask import Flask, request, jsonify

app = Flask(__name__)

IS_PATCHED: dict[str, bool] = {
    "xss": False,
    "admin_exposure": False,
    "info_disclosure": False,
}

NODE_NAME = os.getenv("NODE_NAME", "web_server")
PORT = int(os.getenv("PORT", 5001))


@app.route("/health")
def health() -> tuple:
    return jsonify({"status": "ok", "node": NODE_NAME, "patched": IS_PATCHED}), 200


@app.route("/info")
def info() -> tuple:
    if not IS_PATCHED["info_disclosure"]:
        return jsonify({"server": "Apache/2.4", "version": "2.4.1", "config": "debug=true"}), 200
    return jsonify({"message": "endpoint secured"}), 200


@app.route("/search", methods=["POST"])
def search() -> tuple:
    q = request.args.get("q", "")
    if not IS_PATCHED["xss"]:
        return jsonify({"results": f"<b>Results for: {q}</b>"}), 200
    return jsonify({"results": "sanitised"}), 200


@app.route("/admin")
def admin() -> tuple:
    if not IS_PATCHED["admin_exposure"]:
        return jsonify({"message": "admin access granted", "users": ["root", "admin"]}), 200
    return jsonify({"error": "403 forbidden"}), 403


@app.route("/state")
def state() -> tuple:
    return jsonify({"node": NODE_NAME, "port": PORT, "patched": IS_PATCHED}), 200


@app.route("/reset")
def reset() -> tuple:
    global IS_PATCHED
    IS_PATCHED = {"xss": False, "admin_exposure": False, "info_disclosure": False}
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
