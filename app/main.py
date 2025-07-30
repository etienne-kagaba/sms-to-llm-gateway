from fastapi import FastAPI, Request
import logging
import time

app = FastAPI()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sms-to-llm-gateway")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000
    status = response.status_code
    method = request.method
    url = request.url.path
    user_agent = request.headers.get("user-agent", "Unknown")

    if status >= 400:
        logger.warning(f"⚠️ {method} {url} - {status}"
                       f" - {duration_ms:.2f}ms - {user_agent}")
    else:
        # Using logger.info since Python
        # logging doesn't have 'http' level by default
        logger.info(f"📡 {method} {url} - {status} - "
                    f"{duration_ms:.2f}ms - {user_agent}")

    return response


@app.get("/")
def send_message():
    return {"message": "Hello, FastAPI with Pipenv!"}
