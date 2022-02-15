import time
from urllib import parse

import requests


class OneDrive(object):
    CLIENT_ID = ["78d4dc35-7e46-42c6-9023-2d39314433a5", "dfe36e60-6133-48cf-869f-4d15b8354769"]
    CLIENT_SECRET = ["ZudGl-p.m=LMmr3VrKgAyOf-WevB3p50", "H0-1:6.Sb8:WCW/J-c]K@fddCt[i0EZ2"]
    OAUTH_HOST = ["https://login.microsoftonline.com", "https://login.partner.microsoftonline.cn"]
    API_HOST = ["https://graph.microsoft.com", "https://microsoftgraph.chinacloudapi.cn"]
    REDIRECT_HOST = ["http://localhost/onedrive-login", "http://localhost/onedrive-login"]

    def __init__(self, is_cn=0):
        self.client_id = OneDrive.CLIENT_ID[is_cn]
        self.client_secret = OneDrive.CLIENT_SECRET[is_cn]
        self.oauth_host = OneDrive.OAUTH_HOST[is_cn]
        self.api_host = OneDrive.API_HOST[is_cn]
        self.redirect_host = OneDrive.REDIRECT_HOST[is_cn]
        self._token = {
            "refresh": "",
            "access": "",
            "expire": 0
        }

    def gen_header(self, access_token=None):
        header = {
            "User-Agent": "ISV|OneList/1.1",
            "Accept": "application/json; odata.metadata=none",
        }
        if access_token is not None:
            header.update({"Authorization": "Bearer " + access_token})
        return header

    def gen_data(self, grant_type):
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_host,
            "grant_type": grant_type,
            "scope": "User.Read Files.ReadWrite.All offline_access",
        }

    def gen_path(self, path):
        _path = str(path).strip(":").split(":", 1)[-1]
        while "//" in _path:
            _path = str(_path).replace("//", "/")
        if _path == "/":
            return _path
        else:
            return str(":/{}:").format(str(_path).strip("/"))

    def do_refresh_token(self, code=None, refresh_token=None):
        if code is None and refresh_token is None:
            refresh_token = self.get_token(key="refresh")
        if code is not None:
            req_data = self.gen_data("authorization_code")
            req_data.update({"code": code})
        else:
            req_data = self.gen_data("refresh_token")
            req_data.update({"refresh_token": refresh_token})
        rep = requests.post(url=self.oauth_host + "/common/oauth2/v2.0/token",
                            data="&".join([str("{}={}").format(item, req_data[item]) for item in req_data]),
                            headers=self.gen_header(),
                            timeout=6).json()
        if "refresh_token" not in rep or "access_token" not in rep:
            print(rep)
            return False
        self._token.update({
            "refresh": rep["refresh_token"],
            "access": rep["access_token"],
            "expire": time.time() + rep["expires_in"]
        })
        return True

    def get_token(self, key=None):
        if key is None:
            return self._token.copy()
        if key in self._token:
            return self._token[key]
        return None

    def get_list(self, file_id):
        url = str(
            self.api_host
            + "/v1.0/me/drive/root{}?expand=children($select=name,size,file,folder,parentReference,lastModifiedDateTime)"
        ).format(parse.quote(self.gen_path(file_id)))
        rep = requests.get(url=url,
                           headers=self.gen_header(access_token=self.get_token("access")),
                           timeout=6).json()
        if "error" in rep:
            print(rep["error"]["message"])
            return []
        return rep

    def get_download_url(self, file_id):
        rep = self.get_list(file_id=file_id)
        return rep.get("@microsoft.graph.downloadUrl")
