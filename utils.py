import asyncio
import functools
import json
import os
from email.utils import formatdate
from typing import Callable, Awaitable, TypeVar, ParamSpec

http_status = {
    200: b"Ok",
    204: b"No Content",
    304: b"Not Modified",
    404: b"Not Found",
    400: b"Bad Request"

}
with open("settings.json", 'r', encoding="utf-8") as file:
    settings = json.load(file)

errors_bodies = {}
for filename in os.listdir(os.path.join(".", settings["ERROR_BODIES"])):
    p = os.path.join(".", settings["ERROR_BODIES"], filename)
    if os.path.isfile(p):
        with open(p, "rb") as file:
            errors_bodies[filename] = file.read()

DIR = os.path.join(b".", settings["DIR"].encode('utf-8'))

args_ = ParamSpec("args_")
o_ = TypeVar("o_")


def to_async(func: Callable[args_, o_]) -> Callable[args_, Awaitable[o_]]:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.get_running_loop().run_in_executor(None, functools.partial(func, *args,
                                                                                        **kwargs))

    return wrapper


def get_header():
    headers = {}
    for key, value in settings["HEADERS"].items():
        headers[key.capitalize().encode("utf-8")] = value.encode("utf-8")

    headers[b"Date"] = formatdate(usegmt=True).encode("utf-8")
    return headers


@to_async
def open_path(path: bytes) -> bytes:
    if path.startswith(b"/"):
        path = path[1:]
    for part in path.split(b"/"):
        if part == b"" or part == b"." or part == b".." or b":" in path:
            raise ValueError

    path = os.path.join(DIR, path)
    if os.path.isdir(path):
        if not settings["SHOW_DIR"]:
            raise FileNotFoundError
        # TODO: add path
    if os.path.isfile(path):
        with open(path, "rb") as fb:
            return fb.read()  # TODO: chunking

    raise FileNotFoundError
