import json

import aiohttp_jinja2
from aiohttp import WSMessage, WSMsgType, web
from jinja2 import FileSystemLoader

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


# @aiohttp_jinja2.template("builds.html")
# async def builds(request):  # pylint: disable=unused-argument
#     build_list = Manager.list_builds()  # pylint: disable=redefined-outer-name
#     logger.debug(build_list)
#     await logger.complete()
#     return {"builds": build_list}


@routes.get("/page/{page}")
@routes.get("/")
@routes.get("/builds")
@aiohttp_jinja2.template("builds.html")
async def page(request):  # pylint: disable=unused-argument
    try:
        page = int(request.match_info.get("page", 1))
        assert page > 0
    except ValueError:
        raise web.HTTPError(reason="Invalid page number")
    except AssertionError:
        raise web.HTTPError(reason="Page number needs to be greater than 0")

    build_list = Manager.list_builds(page=page)  # pylint: disable=redefined-outer-name
    logger.debug(build_list)
    await logger.complete()

    return {
        "builds": build_list,
        "pages": Manager.get_all_pages(),
        "pagination_current": page,
        "pagination_per_page": Manager.per_page,
        "pagination_next": page + 1,
        "pagination_prev": page - 1,
        "pagination_last_page": Manager.last_page(),
        "pagination_build_count_total": Manager.total_build_count(),
    }


@routes.get("/favicon.ico")
async def favicon(request):
    return web.FileResponse("wbld/static/images/favicon.ico")


@routes.get("/build/{uuid}")
@aiohttp_jinja2.template("build.html")
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
