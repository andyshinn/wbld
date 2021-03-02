from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

sentry_sdk.init(integrations=[AioHttpIntegration()])

load_dotenv()
