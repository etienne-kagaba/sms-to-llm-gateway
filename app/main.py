from app.config import (
    SMS_GATEWAY_PUBLIC_USER,
    SMS_GATEWAY_PUBLIC_PASSWORD,
    CURRENT_PHONE)


from fastapi import FastAPI, Request, Response, status, Depends
from fastapi.responses import JSONResponse
import logging
import time
import base64


from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db, engine, Base
from contextlib import asynccontextmanager


from app.utils.validation import validate_android
from app.services.sms_service import send_sms
from app.services.conversation_service import save_conversation
from app.services.llm_service import get_context, get_gemini_response


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

server = FastAPI(lifespan=lifespan)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sms-to-llm-gateway")


@server.middleware("http")
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
        logger.info(f"📡 {method} {url} - {status} - "
                    f"{duration_ms:.2f}ms - {user_agent}")

    return response


@server.get("/")
def send_message():
    return {"message": "Hello, welcome to SMS-To-LLM Gateway!"}


@server.post("/sms-webhook")
async def sms_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Processing new request")

    validation_result = await validate_android(request)
    if isinstance(validation_result, Response):
        return validation_result
    validation_result = await request.json()

    payload = validation_result.get("payload", validation_result)
    message: str = payload.get("message")
    phone_number: str = (payload.get("phoneNumber")
                         or payload.get("phone_number"))

    if not phone_number.startswith("+250"):
        return Response(
            "Only Rwandan phone numbers are supported",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if phone_number == CURRENT_PHONE:
        return Response(
            "AI can not text its self",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        context = await get_context(db, phone_number)

        gemini_response = await get_gemini_response(message, context)

        credentials = (f"{SMS_GATEWAY_PUBLIC_USER}:"
                       f"{SMS_GATEWAY_PUBLIC_PASSWORD}")
        credentials_bytes = credentials.encode("utf-8")
        base64_bytes = base64.b64encode(credentials_bytes)
        base64_str = base64_bytes.decode("utf-8")

        auth_header = f"Basic {base64_str}"

        send_result = await send_sms(
            phone_number,
            gemini_response,
            auth_url=auth_header
        )

        if send_result["error"]:
            raise Exception(send_result['error'])

        await save_conversation(
            db,
            phone_number,
            message,
            gemini_response,
            language="en",
        )

        return JSONResponse(
            {
                "status": "success",
                "message": "SMS sent successfully",
                "geminiResponse": gemini_response,
            },
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return Response(
            "Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
