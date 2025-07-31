# 📡 smstollm

**smstollm** is a lightweight FastAPI service that receives SMS messages from an Android device via webhook, sends responses using an LLM (like Gemini), and returns them via SMS. The app is containerized and designed to run on distributed hosts behind a load balancer.


## 📦 Docker Image

* **Docker Hub:** [kagaba/smstollm](https://hub.docker.com/r/kagaba/smstollm)
* **Tags:**

  * `v1`: First stable release
  * `latest`: Most recent build


## 🔧 Environment Variables

The app uses the following environment variables, passed via a `.env` file or `--env` flags when running:

```env
# Required for verifying if the request is comming from Android SMS Gateway
SMS_GATEWAY_SIGNING_KEY=

# Required for getting AI generated Responses
GEMINI_API_KEY=

# Required to avoid infinite loop of AI texting itself
CURRENT_PHONE=

# Auth credentials for Android SMS Gateway (these are provided by the android app)
SMS_GATEWAY_PUBLIC_USER=
SMS_GATEWAY_PUBLIC_PASSWORD=

# Database URL
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
```

## 🤖 Android SMS Gateway Integration

This app is designed to work with [Android SMS Gateway](https://github.com/capcom6/android-sms-gateway) by [capcom6](https://github.com/capcom6). You’ll need:

* An Android device with the SMS Gateway app installed.
* The app set to Cloud Server mode.
* Use the credentials to register a webhook

Note: The webhook will be wherever you will host this application + the `/sms-webhook` endpoint. For example: `https:<mydomain>/sms-webhook`. If testing locally, you can use ngrok to expose your application, and use the url provided by ngrok together with the endpoint as a webhook.

### ✅ Setup Guide

1. Download the app: [Releases page](https://github.com/capcom6/android-sms-gateway/releases)
2. Enable **Cloud Server** mode.
3. Retrieve:

   * `SMS_GATEWAY_PUBLIC_USER`
   * `SMS_GATEWAY_PUBLIC_PASSWORD`
4. Register a webhook:

```bash
curl -X POST -u <username>:<password> \
  -H "Content-Type: application/json" \
  -d '{ "id": "smstollm-hook", "url": "https://<your-server>/sms-webhook", "event": "sms:received" }' \
  https://api.sms-gate.app/3rdparty/v1/webhooks
```

---

## 🏗 Build Locally

Clone this repo and build the Docker image:

```bash
docker build -t kagaba/smstollm:v1 .
```

Run locally with your `.env`:

```bash
docker run --env-file .env -p 8080:8080 kagaba/smstollm:v1
```

Test:

```bash
curl http://localhost:8080/
```

You should see a response like this
```json
{
    "message": "Hello, welcome to SMS-To-LLM Gateway!"
}
```

## 🧪 Testing with Docker Compose

To quickly spin up the SMS-to-LLM Gateway application with load balancing for testing purposes, use the included `docker-compose.yml` file.

### Prerequisites

* Docker and Docker Compose installed on your system.
* `.env` file with necessary environment variables in the project root.
* `haproxy.cfg` configuration file in the project root.

### Steps

1. Open a terminal in the project root directory (where `docker-compose.yml` is located).

2. Run the following command to start the application stack in detached mode:

   ```bash
   docker-compose up -d
   ```

3. This will start:

   * Two backend containers `web01` and `web02` running your app.
   * One HAProxy load balancer container `lb01` listening on host port `8080`.

4. You can test the load balancer by sending requests to:

   ```
   http://localhost:8080/
   ```

   The requests will be balanced between `web01` and `web02`.

   ![alt text](<assets/Screenshot from 2025-07-31 05-36-54.png>)

5. To view logs for all services:

   ```bash
   docker-compose logs -f
   ```

6. To stop and remove all containers, network, and volumes created by Compose:

   ```bash
   docker-compose down
   ```
## 🚀 Run on Production Hosts (`web-01` and `web-02`)
1. Create an `.env` file on each host at `/etc/smstollm/.env` with all necessary variables as described above.

2. SSH into both hosts and run:

    ```bash
    docker pull kagaba/smstollm:v1

    docker run -d --name smstollm --restart unless-stopped \
    --env-file /etc/smstollm/.env \
    -p 8080:8080 kagaba/smstollm:v1
    ```

## 🔁 Load Balancer (HAProxy)

Edit `/etc/haproxy/haproxy.cfg` and add:

```haproxy
frontend http_front
    bind *:80
    default_backend smstollm_back

backend smstollm_back
    balance roundrobin
	option httpchk GET /
	http-check expect status 200
    server web01 web01:8080 check inter 2000 rise 3 fall 3
    server web02 web02:8080 check inter 2000 rise 3 fall 3
```

Reload HAProxy:

```bash
docker exec -it lb-01 sh -c 'haproxy -sf $(pidof haproxy) -f /etc/haproxy/haproxy.cfg'
```

## 🙌 Credits

* **Android SMS Gateway** by [capcom6](https://github.com/capcom6)
  ↳ [GitHub](https://github.com/capcom6/android-sms-gateway)
  ↳ [Docs](https://docs.sms-gate.app)
