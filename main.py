from os.path import join
import asyncio
from collections import defaultdict
import hashlib
from utils import http_status, settings, open_path, get_header

with open(join('.', settings['INDEX']), 'rb') as index_file:
    index = index_file.read()


async def handle_http(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    if reader.at_eof():
        writer.close()
        await writer.wait_closed()
        return
    method = (await reader.readuntil(b' '))[:-1].upper()
    path = (await reader.readuntil(b' '))[:-1]
    version = (await reader.readuntil(b'\r\n'))[:-2]
    if version != b"HTTP/1.1":
        raise
    headers = defaultdict(list)
    while True:
        header = (await reader.readuntil(b'\r\n')).strip()
        if not header:
            break
        key, value = header.split(b":", 1)
        headers[key.strip().upper()].append(value.strip())
    response = b""
    etag = b""
    if method in (b'GET', b'HEAD'):
        path = path.split(b"?", 1)[0].split(b"#", 1)[0]
        print(repr(path))
        if path in (b"", b"/"):
            response = index
            status = 200
        else:
            try:
                response = await open_path(path)
            except FileNotFoundError:
                # response = errors_bodies["404.html"]
                status = 404
            except ValueError:
                # response = errors_bodies['invalid_path.html']
                status = 400
            else:
                status = 200 if response else 204
    elif method in (b"POST", b"PUT", b"DELETE", b"CONNECT", b"OPTIONS", b"TRACE", b"PATCH"):
        status = 405
    else:
        status = 400

    if status == 200:
        h = hashlib.sha256()
        h.update(response)
        etag = b'"' + h.hexdigest().encode("utf-8") + b'"'
        if etag == headers.get("IF-NONE-MATCH"):
            status = 304
            response = b""

    writer.write(b"HTTP/1.1 " + str(status).encode("utf-8") + b' ' + http_status[status] + b"\r\n")
    res_headers = get_header()
    if etag:
        res_headers[b"ETag"] = etag
    for key, value in res_headers.items():
        writer.write(key + b": " + value + b"\r\n")
    writer.write(b"\r\n" + response)
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_http, settings["HOST"], settings["PORT"])
    print(f"listening on {settings['HOST']}:{settings['PORT']}")
    async with server:
        await server.serve_forever()


asyncio.run(main())
