import base64
import json
import time

import requests


class AliyunDrive:
    ROOT_API = "https://api.aliyundrive.com"
    ROOT_PATH = "root"

    def __init__(self, refreshToken):
        self._token = {
            "refresh": refreshToken,
            "access": "",
            "drive_id": "",
            "type": "Bearer",
            "expire": 0,
        }

    def gen_header(self, auth=True, accessToken=None):
        if accessToken is None:
            accessToken = self.get_token("access")
        header = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=utf-8",
            "Origin": "https://www.aliyundrive.com",
            "Referer": "https://www.aliyundrive.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:94.0) Gecko/20100101 Firefox/94.0",
        }
        if auth is True:
            header.update({"Authorization": f"{self.get_token('type')} {accessToken}"})
        return header

    def do_refresh_token(self, refreshToken=None):
        if refreshToken is None:
            refreshToken = self._token["refresh"]
        rep = requests.post(
            "https://auth.aliyundrive.com/v2/account/token",
            headers=self.gen_header(auth=False),
            json={
                "refresh_token": refreshToken,
                "grant_type": "refresh_token",
            },
            timeout=6
        ).json()
        if "access_token" not in rep:
            print(rep)
            return False
        self._token.update({
            "refresh": rep["refresh_token"],
            "access": rep["access_token"],
            "drive_id": rep["default_drive_id"],
            "type": rep["token_type"],
            "expire": time.time() + rep["expires_in"]
        })
        return True

    def get_token(self, key=None):
        if key is None:
            return self._token.copy()
        if key in self._token:
            return self._token[key]
        return None

    def get_list(self, parentFileID="root"):
        rep = requests.post(
            AliyunDrive.ROOT_API + "/adrive/v3/file/list",
            headers=self.gen_header(),
            json={
                "all": False,
                "drive_id": self.get_token("drive_id"),
                "fields": "*",
                "limit": 100,
                "order_by": "name",
                "order_direction": "ASC",
                "parent_file_id": parentFileID,
            },
            timeout=6
        ).json()
        if rep.get("code") == "AccessTokenInvalid":
            if self.do_refresh_token():
                return self.get_list(parentFileID)
            else:
                return []
        r = rep.get("items")
        return r if r is not None else []

    def get_download_url(self, fileID):
        rep = requests.post(
            AliyunDrive.ROOT_API + "/v2/file/get_download_url",
            headers=self.gen_header(),
            json={
                "drive_id": self.get_token("drive_id"),
                "file_id": fileID,
            },
            timeout=6
        ).json()
        return rep.get("url")

    @staticmethod
    def get_userinfo_via_bizext(biz: str):
        biz_ = base64.b64decode(biz.encode()).decode(encoding="ISO-8859-1")
        data = json.loads(biz_)
        return data.get("pds_login_result").get("refreshToken")
