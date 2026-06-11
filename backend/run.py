import uvicorn, os
from dotenv import load_dotenv

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_path, override=True)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=int(os.getenv("BACKEND_PORT", "8008")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )