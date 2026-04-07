import os
from flask import Flask, request, jsonify

app = Flask(__name__)

IS_PATCHED: dict[str, bool] = {
    "sql_injection": False,
    "data_dump": False,
    "unauth_access": False,
}

FAKE_DATA: list[dict] = [
    {"id": 1, "name": "Alice", "salary": 95000, "ssn": "123-45-6789"},
    {"id": 2, "name": "Bob", "salary": 87000, "ssn": "987-65-4321"},
]

NODE_NAME = os.getenv("NODE_NAME", "database_node")
PORT = int(os.getenv("PORT", 5003))


@app.route("/health")
def health() -> tuple:
    return jsonify({"status": "ok", "node": NODE_NAME, "patched": IS_PATCHED}), 200


@app.route("/query")
def query() -> tuple:
    sql = request.args.get("sql", "SELECT 1")
    if not IS_PATCHED["sql_injection"]:
        return jsonify({
            "executed": sql,
            "rows": FAKE_DATA,
            "warning": "unsanitised query",
        }), 200
    return jsonify({"error": "parameterised queries only"}), 400


@app.route("/dump")
def dump() -> tuple:
    if not IS_PATCHED["data_dump"]:
        return jsonify({"records": FAKE_DATA, "count": len(FAKE_DATA)}), 200
    return jsonify({"error": "403 forbidden"}), 403


@app.route("/schema")
def schema() -> tuple:
    if not IS_PATCHED["unauth_access"]:
        return jsonify({
            "tables": ["users", "salaries", "sessions"],
            "columns": {"users": ["id", "name", "ssn", "salary"]},
        }), 200
    return jsonify({"error": "authentication required"}), 401


@app.route("/state")
def state() -> tuple:
    return jsonify({"node": NODE_NAME, "port": PORT, "patched": IS_PATCHED}), 200


@app.route("/reset")
def reset() -> tuple:
    global IS_PATCHED
    IS_PATCHED = {"sql_injection": False, "data_dump": False, "unauth_access": False}
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
