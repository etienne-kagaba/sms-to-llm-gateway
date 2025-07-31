import httpx
from typing import Optional, TypedDict


class SendSMSResult(TypedDict):
    data: Optional[str]
    error: Optional[Exception]


async def send_sms(
        phone_number: str,
        message: str,
        auth_url: str
        ) -> SendSMSResult:
    url = "https://api.sms-gate.app/3rdparty/v1/message"
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": auth_url,
    }
    payload = {
        "message": message,
        "phoneNumbers": [phone_number],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    if not response.is_success:
        return {
            "data": None,
            "error": Exception(f"SMS sending failed: "
                               f"{response.status_code} {response.text}")}

    return {
        "data": response.text,
        "error": None
    }
