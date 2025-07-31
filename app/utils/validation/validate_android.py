import time
import hmac
import hashlib
import json
from fastapi import Request, Response
from app.config import SMS_GATEWAY_SIGNING_KEY as SIGNING_KEY


async def validate_request(request: Request):
    if request.method != "POST":
        return Response(
            "Method Not Allowed",
            status_code=405)

    x_signature = request.headers.get("x-signature")
    x_timestamp = request.headers.get("x-timestamp")
    if not x_signature or not x_timestamp:
        return Response(
            "Missing signature headers",
            status_code=401)

    if not SIGNING_KEY:
        return Response(
            "Server misconfiguration: missing signing key",
            status_code=500)

    body_bytes = await request.body()
    body_string = body_bytes.decode()

    message = body_string + x_timestamp
    computed_signature = hmac.new(
        SIGNING_KEY.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if hmac.compare_digest(computed_signature.lower(), x_signature.lower()):
        return Response("Invalid signature", status_code=401)

    try:
        ts = int(x_timestamp)
    except ValueError:
        return Response("Invalid timestamp", status_code=401)

    now = int(time.time())
    if abs(now - ts) > 300:
        return Response("Invalid or expired timestamp", status_code=401)

    try:
        body = json.loads(body_string)
    except Exception:
        return Response("Invalid JSON payload", status_code=400)

    if body.get("event") != "sms:received":
        return Response("Invalid event type", status_code=400)

    return body
