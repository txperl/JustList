import base64
import hashlib
import os
import re

import requests
import rsa


class cloud189(object):
    def __init__(self, uname, upsw):
        self.RSA_KEY = """-----BEGIN PUBLIC KEY-----
        MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDY7mpaUysvgQkbp0iIn2ezoUyh
        i1zPFn0HCXloLFWT7uoNkqtrphpQ/63LEcPz1VYzmDuDIf3iGxQKzeoHTiVMSmW6
        FlhDeqVOG094hFJvZeK4OzA6HVwzwnEW5vIZ7d+u61RV1bsFxmB68+8JXs3ycGcE
        4anY+YzZJcyOcEGKVQIDAQAB
        -----END PUBLIC KEY-----
        """
        self.b64map = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        self.BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")
        self.username = uname
        self.password = upsw
        self.session = None

    def encrypt(self, password: str) -> str:
        return base64.b64encode(
            rsa.encrypt(
                (password).encode("utf-8"),
                rsa.PublicKey.load_pkcs1_openssl_pem(self.RSA_KEY.encode()),
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
        r = self.session.get(
            "https://cloud.189.cn/api/portal/loginUrl.action?pageId=1&redirectURL=https://cloud.189.cn/main.action"
        )
        captchaToken = re.findall(r"captchaToken' value='(.+?)'", r.text)[0]
        lt = re.findall(r'lt = "(.+?)"', r.text)[0]
        returnUrl = re.findall(r"returnUrl = '(.+?)'", r.text)[0]
        paramId = re.findall(r'paramId = "(.+?)"', r.text)[0]
        self.session.headers.update({"lt": lt})
        return captchaToken, returnUrl, paramId

    def md5(self, s):
        hl = hashlib.md5()
        hl.update(s.encode(encoding="utf-8"))
        return hl.hexdigest()

    def needcaptcha(self, captchaToken):
        r = self.session.post(
            url="https://open.e.189.cn/api/logbox/oauth2/needcaptcha.do",
            data={
                "accountType": "01",
                "userName": "{RSA}" + self.b64tohex(self.encrypt(self.username)),
                "appKey": "cloud",
            },
        )
        if r.text == "0":
            # DONT NEED CAPTCHA
            return ""
        else:
            print("需要输入验证码")
            r = self.session.get(
                url="https://open.e.189.cn/api/logbox/oauth2/picCaptcha.do",
                params={"token": captchaToken},
            )
            with open("./captcha.png", "wb") as f:
                f.write(r.content)
                f.close()
            return input("验证码下载完成，打开 ./captcha.png 查看: ")

    def login(self, token=None):
        self.session = requests.session()
        self.session.headers.update(
            {
                "Referer": "https://open.e.189.cn/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            }
        )
        if token is not None:
            try:
                tmp = token.copy()
                if "outdated" in token:
                    del tmp["outdated"]
                [
                    self.session.cookies.set(k, v, domain=".cloud.189.cn")
                    for k, v in tmp.items()
                ]
                r = self.session.get("https://cloud.189.cn/v2/getUserLevelInfo.action")
                assert "InvalidSessionKey" not in r.text and "登陆框面板" not in r.text
                return token
            except:
                print("[cloud189] token error, try to login")
                self.session = requests.session()
                self.session.headers.update(
                    {
                        "Referer": "https://open.e.189.cn/",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
                    }
                )
        captchaToken, returnUrl, paramId = self.redirect()
        validateCode = self.needcaptcha(captchaToken)
        r = self.session.post(
            url="https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do",
            data={
                "appKey": "cloud",
                "accountType": "01",
                "userName": "{RSA}" + self.b64tohex(self.encrypt(self.username)),
                "password": "{RSA}" + self.b64tohex(self.encrypt(self.password)),
                "validateCode": validateCode,
                "captchaToken": captchaToken,
                "returnUrl": returnUrl,
                "mailSuffix": "@189.cn",
                "paramId": paramId,
            },
        )
        msg = r.json()["msg"]
        if msg == "登录成功":
            self.session.get(r.json()["toUrl"])
            return self.session.cookies.get_dict()
        else:
            print(msg)
            os._exit(0)

    def get_file_size_str(self, filesize: int) -> str:
        if 0 < filesize < 1024 ** 2:
            return f"{round(filesize / 1024, 2)} KB"
        elif 1024 ** 2 < filesize < 1024 ** 3:
            return f"{round(filesize / 1024 ** 2, 2)} MB"
        elif 1024 ** 3 < filesize < 1024 ** 4:
            return f"{round(filesize / 1024 ** 3, 2)} GB"
        elif 1024 ** 4 < filesize < 1024 ** 5:
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
                    "noCache": 0
                },
                headers={"Accept": "application/json;charset=UTF-8"},
                timeout=6,
            ).json()
        except:
            return []
        if "fileListAO" not in rep:
            return []
        rep = rep["fileListAO"]
        r = []
        for type_ in ("folderList", "fileList"):
            for x in rep[type_]:
                r.append({
                    "isFolder": type_ == "folderList",
                    "createTime": x["createDate"],
                    "lastOpTime": x["lastOpTime"],
                    "parentId": fileId,
                    "fileId": x["id"],
                    "fileName": x["name"],
                    "fileSize": x["size"] if type_ == "fileList" else 0,
                    "fileType": x["name"].split(".")[-1],
                })
        return r

    def get_file_info(self, fileid, dl=False):
        try:
            r = self.session.get(
                "https://cloud.189.cn/api/open/file/getFileDownloadUrl.action",
                params={
                    "fileId": fileid,
                    "noCache": 0
                },
                headers={"Accept": "application/json;charset=UTF-8"},
                timeout=6
            ).json()
        except:
            return False
        if not dl:
            return r
        if "fileDownloadUrl" in r:
            return r["fileDownloadUrl"]
        return False
