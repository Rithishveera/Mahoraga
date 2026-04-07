import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME: str = "Mahoraga"
APP_TAGLINE: str = "Adapts to every attack. Never defeated by the same technique twice."
APP_VERSION: str = "1.0.0"

NETWORK_NODES: dict[str, dict] = {
    "web_server": {"url": "http://localhost:5001", "port": 5001, "protected": False},
    "api_service": {"url": "http://localhost:5002", "port": 5002, "protected": True},
    "database_node": {"url": "http://localhost:5003", "port": 5003, "protected": True},
    "admin_panel": {"url": "http://localhost:5004", "port": 5004, "protected": False},
}

PROTECTED_SERVICES: list[str] = ["api_service", "database_node"]
CRITICAL_ACTIONS: list[str] = [
    "shutdown", "block_all_traffic", "delete_service", "wipe_data",
]

RISK_THRESHOLD: int = int(os.getenv("RISK_THRESHOLD", "70"))
RED_TRAINING_STEPS: int = int(os.getenv("RED_TRAINING_STEPS", "50000"))
BLUE_RETRAIN_INTERVAL: int = int(os.getenv("BLUE_RETRAIN_INTERVAL", "100"))
DB_PATH: str = os.getenv("DB_PATH", "data/threat_memory.db")
BASELINE_CSV: str = os.getenv("BASELINE_CSV", "data/baseline_traffic.csv")
MODELS_DIR: str = "data/models"

USE_LLM_REPORTS: bool = os.getenv("USE_LLM_REPORTS", "true").lower() == "true"
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
ALLOWED_ORIGINS: list[str] = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")
