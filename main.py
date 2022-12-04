import socket as s
from os import path
import re

srv = s.socket(s.AF_INET, s.SOCK_STREAM)
srv.bind(('', 2000))
hrp_re = re.compile(r"(?P<method>[^ \n\r]+) (?P<url>[^ \n\r]+) (?P<version>[^ \n\r]+)\r\n"
                    r"(?P<heads>([^\r\n]+\r\n)*)\r\n(?P<data>(.*\n?)*)"
)
public_html = path.join(path.dirname(__file__), "public_html")
srv.listen(1)
print("ready")

# http request parser
def hrp(data):
    if not data:
        return {
            "method": "",
            "url": "",
            "version": "",
            "header": {},
            "data": "",
        }
    print(data)
    match = hrp_re.match(data)
    header = {}
    heads =match.group("heads")
    for item in heads.split("\r\n")[:-1]:
        item = item.split(": ")
        header[item[0]] = item[1]

    return {
        "method": match.group("method"),
        "url": match.group("url"),
        "version": match.group("version"),
        "header": header,
        "data": match.group("data"),
    }

# http reponse maker
def hrm(version: str, status_code: int, message: str, header: dict, body: bytes):
    header["Content-Length"] = len(body)
    header_str = "".join((f"{key}: {value}\r\n" for key, value in header.items()))
    return f"{version} {status_code} {message}\r\n{header_str}\r\n".encode("utf-8") + body

while True:
    cli, addr = srv.accept()
    data = hrp(cli.recv(1024).decode("utf"))
    print(data["version"])
    if data["url"] == "/":
        url = public_html + "/index.html"
    else:
        url = public_html + data["url"]
    
    try:
        file=  open(url, "rb")
    except Exception:
        print("not found")
        file=open(public_html + "/404.html", "rb")
        status = (404,"not found")
    else:
        print("ok")
        status = (200, "ok")
    
    cli.send(hrm(data["version"], status[0], status[1], data["header"], file.read()))
    cli.close()
