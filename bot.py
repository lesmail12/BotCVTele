from telegram.ext import Application
import os
import httpx

# Config
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8000))
WEBHOOK_MODE = os.getenv("RAILWAY_ENV") == "production"

# HTTP Client config
httpx_client = httpx.AsyncClient(
    timeout=60.0,
    limits=httpx.Limits(max_connections=1)  # ⚠️ Penting!
)

async def post_init(app: Application):
    app.bot._client = httpx_client

async def post_shutdown(app: Application):
    await httpx_client.aclose()

if __name__ == "__main__":
    application = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    if WEBHOOK_MODE:
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"https://{os.getenv('RAILWAY_STATIC_URL')}/{TOKEN}",
            http_version="1.1",
            allowed_updates=Update.ALL_TYPES
        )
    else:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            close_loop=True,
            stop_signals=[SIGTERM, SIGABRT]  # Handle shutdown properly
        )