from aiohttp import web
from jinja2 import FileSystemLoader
import aiohttp_jinja2

from wbld.build import Manager, STORAGE

routes = web.RouteTableDef()
app = web.Application()

aiohttp_jinja2.setup(app, loader=FileSystemLoader("wbld/templates"))


@routes.get("/")
@aiohttp_jinja2.template("builds.html")
async def builds(request):  # pylint: disable=unused-argument
    manager = Manager()
    builds = manager.list_builds()  # pylint: disable=redefined-outer-name
    return {"builds": builds}


@routes.get("/build/{uuid}")
@aiohttp_jinja2.template("build.html")
async def build(request):  # pylint: disable=unused-argument
    manager = Manager()
    build = manager.get_build(request.match_info["uuid"])  # pylint: disable=redefined-outer-name
    return {"build": build}


routes.static("/static", "wbld/static")
routes.static("/data", STORAGE)

if __name__ == "__main__":
    app.add_routes(routes)
    web.run_app(app=app, host="0.0.0.0", port=8090)
