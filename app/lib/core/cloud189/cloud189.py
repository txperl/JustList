import urllib.parse
import base64

import requests
import rsa


class cloud189(object):
    def __init__(self, uname, upsw):
        self.b64map = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        self.BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")
        self.username = uname
        self.password = upsw
        self.session = None

    def encrypt(self, content: str, rsa_key: str) -> str:
        rsa_key = (
            "-----BEGIN PUBLIC KEY-----\n" + rsa_key + "\n-----END PUBLIC KEY-----"
        )
        return base64.b64encode(
            rsa.encrypt(
                (content).encode("utf-8"),
                rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode()),
            )
        ).decode()

    def int2char(self, a):
        return self.BI_RM[a]

    def b64tohex(self, a):
        d = ""
        e = 0
        for i in range(len(a)):
            if list(a)[i] != "=":
                v = self.b64map.index(list(a)[i])
                if 0 == e:
                    e = 1
                    d += self.int2char(v >> 2)
                    c = 3 & v
                elif 1 == e:
                    e = 2
                    d += self.int2char(c << 2 | v >> 4)
                    c = 15 & v
                elif 2 == e:
                    e = 3
                    d += self.int2char(c)
                    d += self.int2char(v >> 2)
                    c = 3 & v
                else:
                    e = 0
                    d += self.int2char(c << 2 | v >> 4)
                    d += self.int2char(15 & v)
        if e == 1:
            d += self.int2char(c << 2)
        return d

    def redirect(self):
        redirect_rep = self.session.get(
            "https://cloud.189.cn/api/portal/loginUrl.action?redirectURL=https%3A%2F%2Fcloud.189.cn%2Fmain.action"
        )
        # appid
        redirect_url = redirect_rep.url
        assert redirect_url != "https://cloud.189.cn/web/main"
        parsed_url = urllib.parse.urlparse(redirect_url)
        appid = urllib.parse.parse_qs(parsed_url.query)["appId"][0]
        headers = {
            "origin": "https://open.e.189.cn",
            "referer": redirect_url,
            "lt": urllib.parse.parse_qs(parsed_url.query)["lt"][0],
            "reqid": urllib.parse.parse_qs(parsed_url.query)["reqId"][0],
        }
        # appconf
        conf = self.session.post(
            "https://open.e.189.cn/api/logbox/oauth2/appConf.do",
            headers=headers,
            files={"version": (None, "2.0"), "appKey": (None, appid)},
        ).json()
        assert conf["result"] == "0"
        conf_encrypt = self.session.post(
            "https://open.e.189.cn/api/logbox/config/encryptConf.do",
            headers=headers,
            files={"appKey": (None, appid)},
        ).json()
        assert conf_encrypt["result"] == 0
        return appid, headers, conf, conf_encrypt

    def renew_token(self, token: dict):
        assert token is not None
        tmp = token.copy()
        if "outdated" in token:
            del tmp["outdated"]
        [self.session.cookies.set(k, v, domain=".cloud.189.cn") for k, v in tmp.items()]
        r = self.session.get("https://cloud.189.cn/v2/getUserLevelInfo.action")
        assert "InvalidSessionKey" not in r.text and "登陆框面板" not in r.text
        return token

    def login(self, token: dict = None):
        # 尝试刷新 Cookie
        try:
            return self.renew_token(token)
        except Exception as e:
            print("[Cloud189] token error, try to login")
        # 尝试使用账号、密码登录
        self.session = requests.session()
        self.session.headers.update(
            {
                "Referer": "https://open.e.189.cn/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            }
        )
        # Reference: https://github.com/alist-org/alist/blob/ca5a53fc24d63d726a23662dfb0bc74e512013a5/drivers/189/login.go
        try:
            # 获取登录请求的必要参数
            appid, headers, conf, conf_encrypt = self.redirect()
            # 登录
            login_rep = self.session.post(
                "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do",
                headers=headers,
                files={
                    "version": (None, "v2.0"),
                    "apToken": (None, ""),
                    "appKey": (None, appid),
                    "accountType": (None, conf["data"]["accountType"]),
                    "userName": (
                        None,
                        conf_encrypt["data"]["pre"]
                        + self.b64tohex(
                            self.encrypt(self.username, conf_encrypt["data"]["pubKey"])
                        ),
                    ),
                    "epd": (
                        None,
                        conf_encrypt["data"]["pre"]
                        + self.b64tohex(
                            self.encrypt(self.password, conf_encrypt["data"]["pubKey"])
                        ),
                    ),
                    "captchaType": (None, ""),
                    "validateCode": (None, ""),
                    "smsValidateCode": (None, ""),
                    "captchaToken": (None, ""),
                    "returnUrl": (None, conf["data"]["returnUrl"]),
                    "mailSuffix": (None, conf["data"]["mailSuffix"]),
                    "dynamicCheck": (None, "FALSE"),
                    "clientType": (None, self.int2char(conf["data"]["clientType"])),
                    "cb_SaveName": (None, "3"),
                    "isOauth2": (None, "TRUE" if conf["data"]["isOauth2"] else "FALSE"),
                    "state": (None, ""),
                    "paramId": (None, conf["data"]["paramId"]),
                },
                timeout=6,
            )
            login_data = login_rep.json()
        except Exception as e:
            return False
        if login_data["result"] == 0:
            self.session.get(login_data["toUrl"])
            return self.session.cookies.get_dict()
        print(login_data["msg"])
        return False

    def get_file_size_str(self, filesize: int) -> str:
        if 0 < filesize < 1024**2:
            return f"{round(filesize / 1024, 2)} KB"
        elif 1024**2 < filesize < 1024**3:
            return f"{round(filesize / 1024 ** 2, 2)} MB"
        elif 1024**3 < filesize < 1024**4:
            return f"{round(filesize / 1024 ** 3, 2)} GB"
        elif 1024**4 < filesize < 1024**5:
            return f"{round(filesize / 1024 ** 4, 2)} TB"
        else:
            return f"{filesize}Bytes"

    def get_files(self, fileId=-11):
        try:
            rep = self.session.get(
                url="https://cloud.189.cn/api/open/file/listFiles.action",
                params={
                    "folderId": fileId,
                    "orderBy": "lastOpTime",
                    "pageNum": 1,
                    "pageSize": 60,
                    "descending": True,
                    "mediaType": 0,
                    "noCache": 0,
                },
                headers={"Accept": "application/json;charset=UTF-8"},
                timeout=6,
            ).json()
            assert "fileListAO" in rep
        except:
            return []
        rep = rep["fileListAO"]
        r = []
        for type_ in ("folderList", "fileList"):
            for x in rep[type_]:
                r.append(
                    {
                        "isFolder": type_ == "folderList",
                        "createTime": x["createDate"],
                        "lastOpTime": x["lastOpTime"],
                        "parentId": fileId,
                        "fileId": x["id"],
                        "fileName": x["name"],
                        "fileSize": x["size"] if type_ == "fileList" else 0,
                        "fileType": x["name"].split(".")[-1],
                    }
                )
        return r

    def get_file_info(self, fileid, dl=False):
        r_v1 = self.get_file_info_v1(fileid, dl)
        if r_v1 is False:
            return self.get_file_info_v2(fileid, dl)
        return r_v1

    def get_file_info_v1(self, fid, dl=True):
        r = self.session.get(
            "https://cloud.189.cn/api/open/file/getFileDownloadUrl.action",
            params={"fileId": fid, "noCache": 0},
            headers={"Accept": "application/json;charset=UTF-8"},
            timeout=6,
        ).json()
        if dl is False:
            return r
        return r.get("fileDownloadUrl", False)

    def get_file_info_v2(self, fid, dl=True):
        r = self.session.get(
            "https://cloud.189.cn/v2/getFileInfo.action",
            params={"fileId": fid, "noCache": 0},
            headers={"Accept": "application/json;charset=UTF-8"},
            timeout=6,
        ).json()
        if dl is False:
            return r
        download_url = "https:" + r.get("downloadUrl", False)
        if download_url is not False:
            final_url = self.session.get(
                download_url, allow_redirects=False, timeout=6
            ).headers["Location"]
            return final_url.replace("http://", "https://")
        return False
