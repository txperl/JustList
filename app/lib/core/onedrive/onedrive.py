# -*- encoding: utf-8 -*-
# Author:  MoeClub.org, github.com/txperl

import json
import time
from urllib import request, error, parse

clientId = [
    "78d4dc35-7e46-42c6-9023-2d39314433a5",
    "dfe36e60-6133-48cf-869f-4d15b8354769",
]
clientSecret = [
    "ZudGl-p.m=LMmr3VrKgAyOf-WevB3p50",
    "H0-1:6.Sb8:WCW/J-c]K@fddCt[i0EZ2",
]
oauthHost = [
    "https://login.microsoftonline.com",
    "https://login.partner.microsoftonline.cn",
]
apiHost = ["https://graph.microsoft.com", "https://microsoftgraph.chinacloudapi.cn"]
redirectHost = ["http://localhost/onedrive-login", "http://localhost/onedrive-login"]


class Utils:
    sizeUnit = (
        ("B", 2 ** 0),
        ("KB", 2 ** 10),
        ("MB", 2 ** 20),
        ("GB", 2 ** 30),
        ("TB", 2 ** 40),
        ("PB", 2 ** 50),
        ("EB", 2 ** 60),
        ("ZB", 2 ** 70),
        ("YB", 2 ** 80),
    )

    @classmethod
    def getSize(cls, size):
        try:
            size = int(size)
        except:
            return "unknown"
        for k, v in cls.sizeUnit:
            if size <= v * 1024:
                return str("{} {}").format(round(size / v, 2), k)
        return "unknown"

    @staticmethod
    def getTime(t=0):
        if t <= 0:
            return int(time.time())
        else:
            return int(int(time.time()) - t)

    @staticmethod
    def formatTime(s="", f="%Y-%m-%d %H:%M:%S"):
        s_ = str(s)
        try:
            return time.strftime(f, time.strptime(s_, "%Y-%m-%dT%H:%M:%SZ"))
        except:
            try:
                return time.strftime(f, time.strptime(s_, "%Y-%m-%dT%H:%M:%S.%fZ"))
            except:
                return "Unknown"

    @staticmethod
    def http(url, method="GET", headers=None, data=None, coding="utf-8", redirect=True):
        method = str(method).strip().upper()
        method_allow = ["GET", "HEAD", "POST", "PUT", "DELETE"]
        if method not in method_allow:
            raise Exception(str("HTTP Method Not Allowed [{}].").format(method))

        class RedirectHandler(request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers):
                pass

            http_error_301 = http_error_303 = http_error_307 = http_error_302

        if headers:
            _headers = headers.copy()
        else:
            _headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": ""}
        if data is not None and method in ["POST", "PUT"]:
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
            data = str(data).encode(coding)
            if "content-length" not in [
                str(item).lower() for item in list(_headers.keys())
            ]:
                _headers["Content-Length"] = str(len(data))
        else:
            data = None
        url_obj = request.Request(url, method=method, data=data, headers=_headers)
        if redirect:
            opener = request.build_opener()
        else:
            opener = request.build_opener(RedirectHandler)
        try:
            res_obj = opener.open(url_obj, timeout=10)
        except error.HTTPError as err:
            res_obj = err
        return res_obj


class OneDrive:
    def __init__(self, refreshToken, rootPath="", redirectUri=redirectHost[0], IS_CN=0):
        self.IS_CN = IS_CN
        self.RootPath = rootPath
        self.redirect_uri = redirectUri
        self.refresh_token = refreshToken
        self.access_token = ""

    @staticmethod
    def accessData(grantType, redirectUri=redirectHost[0], IS_CN=0):
        return {
            "client_id": clientId[IS_CN],
            "client_secret": clientSecret[IS_CN],
            "redirect_uri": redirectUri,
            "grant_type": grantType,
            "scope": "User.Read Files.ReadWrite.All offline_access",
        }

    @staticmethod
    def drivePath(path):
        path = str(path).strip(":").split(":", 1)[-1]
        while "//" in path:
            path = str(path).replace("//", "/")
        if path == "/":
            return path
        else:
            return str(":/{}:").format(str(path).strip("/"))

    @staticmethod
    def getHeader(accessToken=""):
        _header = {
            "User-Agent": "ISV|OneList/1.1",
            "Accept": "application/json; odata.metadata=none",
        }
        if accessToken:
            _header["Authorization"] = str("Bearer {}").format(accessToken)
        return _header

    def getToken(self, respCode):
        data = self.accessData(
            "authorization_code", redirectHost[self.IS_CN], self.IS_CN
        )
        data["code"] = respCode
        Data = "&".join([str("{}={}").format(item, data[item]) for item in data])
        page = Utils.http(
            oauthHost[self.IS_CN] + "/common/oauth2/v2.0/token",
            "POST",
            data=Data,
            headers=self.getHeader(),
        )
        resp = json.loads(page.read().decode())
        if "refresh_token" in resp and "access_token" in resp:
            self.access_token = resp["access_token"]
            self.refresh_token = resp["refresh_token"]
        else:
            raise Exception("Error, Get Refresh Token.")

    def getAccessToken(self, refreshToken=None):
        data = self.accessData(
            "refresh_token", redirectHost[self.IS_CN], IS_CN=self.IS_CN
        )
        if refreshToken is None:
            data["refresh_token"] = self.refresh_token
        else:
            data["refresh_token"] = refreshToken
        Data = "&".join([str("{}={}").format(item, data[item]) for item in data])
        page = Utils.http(
            oauthHost[self.IS_CN] + "/common/oauth2/v2.0/token",
            "POST",
            data=Data,
            headers=self.getHeader(),
        )
        resp = json.loads(page.read().decode())
        if "refresh_token" in resp and "access_token" in resp:
            self.access_token = resp["access_token"]
            self.refresh_token = resp["refresh_token"]
            return resp
        else:
            raise Exception("Error, Get Access Token.")

    def get_file_info(self, fId, dl):
        path = fId
        url = str(
            apiHost[self.IS_CN]
            + "/v1.0/me/drive/root{}?expand=children($select=name,size,file,folder,parentReference,lastModifiedDateTime)"
        ).format(parse.quote(self.drivePath(path)))
        page = Utils.http(url, headers=self.getHeader(self.access_token))
        r = json.loads(page.read().decode())
        if not dl:
            return r
        if "@microsoft.graph.downloadUrl" in r:
            return r["@microsoft.graph.downloadUrl"]
        return False
