import sentry_sdk
from dotenv import load_dotenv
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

sentry_sdk.init(integrations=[AioHttpIntegration()])

load_dotenv()
