from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(body)
            message = data.get("message", "")
        except json.JSONDecodeError:
            message = body

        print(f"收到前端消息: {message}")

        response = {
            "status": "success",
            "received": message
        }

        response_bytes = json.dumps(response, ensure_ascii=False).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_GET(self):
        response = {
            "status": "running",
            "message": "后端服务正常运行"
        }

        response_bytes = json.dumps(response, ensure_ascii=False).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 9826

    server = HTTPServer((host, port), SimpleHandler)
    print(f"服务启动成功: http://{host}:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已关闭")
        server.server_close()