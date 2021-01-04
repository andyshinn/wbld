import asyncio
import json
import sys

import aiohttp


async def main():
    session = aiohttp.ClientSession()

    async with session.ws_connect("http://localhost:8090/ws") as ws:
        await ws.send_json({"action": "build", "state": sys.argv[1]})

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break

    await session.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
