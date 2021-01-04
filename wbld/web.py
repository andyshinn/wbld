import json

from aiohttp import web, WSMsgType, WSMessage
from jinja2 import FileSystemLoader
import aiohttp_jinja2

from wbld.build import Manager, Storage
from wbld.log import logger

routes = web.RouteTableDef()
app = web.Application()

aiohttp_jinja2.setup(app, loader=FileSystemLoader("wbld/templates"))


@routes.get("/ws")
async def websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    await ws.send_str("hi")

    msg: WSMessage
    async for msg in ws:
        # ws.__next__() automatically terminates the loop
        # after ws.close() or ws.exception() is called
        if msg.type == WSMsgType.TEXT:
            data = json.loads(msg.data)
            peername = request.transport.get_extra_info("peername")

            if data["action"] == "join":
                logger.debug(f"Client joined: {peername}")
                request.app["websockets"].append(ws)
            elif data["action"] == "build":
                for _ws in request.app["websockets"]:
                    await _ws.send_json({"action": "build", "state": data["state"]})
            logger.debug(data)
        elif msg.type == WSMsgType.ERROR:
            logger.debug("ws connection closed with exception %s" % ws.exception())

        logger.debug(request.app["websockets"])

    logger.debug("websocket connection closed")
    await logger.complete()

    return ws


@routes.get("/")
@aiohttp_jinja2.template("builds.html.jinja2")
async def builds(request):  # pylint: disable=unused-argument
    build_list = Manager.list_builds()  # pylint: disable=redefined-outer-name
    return {"builds": build_list}


@routes.get("/build/{uuid}")
@aiohttp_jinja2.template("build.html.jinja2")
async def build(request):  # pylint: disable=unused-argument
    build_info = Manager.get_build(request.match_info["uuid"])
    return {"build": build_info}


routes.static("/static", "wbld/static")
routes.static("/data", Storage.base_path)

if __name__ == "__main__":
    Storage.create()
    app.add_routes(routes)
    app["websockets"] = []
    web.run_app(app=app, host="0.0.0.0", port=8090)
