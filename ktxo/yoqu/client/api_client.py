import logging
import logging.config
import requests

logger = logging.getLogger("ktxo.yoqu")


class APIWrapper():
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()

    def _do_request(self, method: str, url, params: dict = None, data: dict = None):
        with self.session as s:
            res = s.request(method, url, params=params, json=data)
            if res.status_code != 200:
                logger.error(f"OPS: {url} {res}")
                logger.error(res.json())
                return res.json()
            return res.json()

    def get_chats(self, resource: str = "chatgpt1") -> list[dict[str, str]]:
        return self._do_request("get",
                                f"{self.base_url}/yoqu/completions/",
                                params={"resource_name": resource})

    def get_chat(self, chat_id, resource: str = "chatgpt1") -> dict:
        return self._do_request("get",
                                f"{self.base_url}/yoqu/completions/{chat_id}",
                                params={"resource_name": resource})

    def update_chat(self, chat_id, prompt: str, resource: str = "chatgpt1") -> dict:
        data = {"chat_id": chat_id, "prompt": prompt, "resource_name": resource}
        return self._do_request("put",
                                f"{self.base_url}/yoqu/completions",
                                data=data)

    def new_chat(self, prompt: str, resource: str = "chatgpt1", delete_after=False) -> dict:
        data = {"prompt": prompt,
                "resource_name": resource,
                "delete_after": delete_after}
        return self._do_request("post",
                                f"{self.base_url}/yoqu/completions",
                                data=data)

    def start_resource(self, resource: str = "chatgpt1") -> dict:
        return self._do_request("post",
                                f"{self.base_url}/admin/start/{resource}")

    def refresh_resource(self, resource: str = "chatgpt1") -> dict:
        return self._do_request("post",
                                f"{self.base_url}/admin/refresh/{resource}")

    def stop_resource(self, resource: str = "chatgpt1") -> dict:
        return self._do_request("post",
                                f"{self.base_url}/admin/stop/{resource}")

    def info_resource(self, resource: str = "chatgpt1"):
        return self._do_request("get",
                                f"{self.base_url}/admin/stats/{resource}")

    def list_resources(self) -> list[str]:
        return self._do_request("get",
                                f"{self.base_url}/admin")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    api = APIWrapper()
    # print(api.get_chats())
    print(api.info_resource())
    # print(api.start_resource())
