import json
import urllib.error
import urllib.request


def send_message(message: str):
    url = "http://127.0.0.1:9826"

    data = json.dumps({
        "message": message
    }).encode("utf-8")

    req = urllib.request.Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            print("后端状态:", result.get("status"))
            print("会话线程:", result.get("thread_id"))
            print("后端回复:", result.get("reply"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8")
        print(f"请求失败({exc.code}): {error_body}")


if __name__ == "__main__":
    while True:
        msg = input("请输入要发送的内容(q退出): ").strip()
        if msg.lower() == "q":
            break
        send_message(msg)
