# coding=utf-8
from ...platform import CMDProcessor
from ..file import main as ifile
from . import onedrive
from urllib import request, error, parse
import threading
import hashlib
import json
import time
import sys
import re
import os


@CMDProcessor.core_register_auto(
    "cloud_onedrive", {"config": "{ROOTPATH}app/core/onedrive/config.json"}
)
class core_module_onedrive(object):
    def __init__(self, info=None):
        self.ENVORON = info["ENVIRON"]
        self.conf = info["config"]
        self.token = {}
        self.api = {}
        self.list = {}
        self.listOutdated = 0
        self.real_id = {}
        self.inCheck = False
        self.lock = threading.Lock()

    def auto(self):
        for u in self.conf["accounts"]:
            is_cn, refreshToken = self.conf["accounts"][u]
            ms = onedrive.OneDrive("", IS_CN=is_cn)
            if refreshToken == "":
                while True:
                    print("进入以下网址以获取 Code 字段")
                    print(
                        f"{onedrive.oauthHost[is_cn]}/common/oauth2/v2.0/authorize?client_id={onedrive.clientId[is_cn]}&response_type=code&redirect_uri={onedrive.redirectHost[is_cn]}&response_mode=query&scope=offline_access%20User.Read%20Files.ReadWrite.All"
                    )
                    print("Code 为跳转后 URL 的 ?code= 到 &session_state 的中间部分")
                    code = str(input("Code: ").strip())
                    if code:
                        break
                ms.getToken(code)
                refreshToken = ms.refresh_token
                self.conf["accounts"][u][1] = refreshToken
            self.api[u] = onedrive.OneDrive(
                refreshToken,
                self.conf["rootPath"],
                onedrive.redirectHost[is_cn],
                is_cn,
            )
            self.token[u] = self.api[u].getAccessToken()
            self.token[u]["outdated"] = time.time() + self.token[u]["expires_in"] - 60
        ifile.io.aout(
            self.ENVORON["ROOTPATH"] + "app/core/onedrive/config.json", self.conf
        )
        t = threading.Timer(0, self.__childth_check)
        t.setDaemon(True)
        t.start()
        return self

    def __childth_check(self):
        tim = time.time()
        print(
            "[onedrive] checking at %s"
            % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tim))
        )
        try:
            self.__update_token(tim)
            if tim > self.listOutdated:
                self.load_list()
        except Exception as e:
            print(e)
        t = threading.Timer(self.conf["sys_checkTime"], self.__childth_check)
        t.setDaemon(True)
        t.start()

    def __update_token(self, tim):
        isUp = False
        for u in self.token.copy():
            if tim > self.token[u]["outdated"]:
                tmp = self.api[u].getAccessToken(self.token[u]["refresh_token"])
                self.lock.acquire()
                self.token[u] = tmp
                self.token[u]["outdated"] = (
                    time.time() + self.token[u]["expires_in"] - 60
                )
                self.conf["accounts"][u][1] = self.token[u]["refresh_token"]
                self.lock.release()
                isUp = True
        if isUp:
            ifile.io.aout(
                self.ENVORON["ROOTPATH"] + "app/core/onedrive/config.json", self.conf
            )

    def load_list(self):
        for u in self.conf["accounts"].copy():
            self.real_id[u] = {}
            tmp = []
            self.__proLoad_list(u, tmp)
            self.lock.acquire()
            self.inCheck = True
            self.list[u] = tmp
            self.inCheck = False
            self.lock.release()
            # print(f"[onedrive] {u} list updated")
        self.listOutdated = time.time() + self.conf["sys_dataExpiredTime"]
        return True

    def __proLoad_list(self, user, arr, path=None):
        if path is None:
            path = self.api[user].RootPath
        url = str(
            onedrive.apiHost[self.api[user].IS_CN]
            + "/v1.0/me/drive/root{}?expand=children($select=name,size,file,folder,parentReference,lastModifiedDateTime)"
        ).format(parse.quote(self.api[user].drivePath(path)))
        page = onedrive.Utils.http(
            url, headers=self.api[user].getHeader(self.api[user].access_token)
        )
        data = json.loads(page.read().decode())
        if "error" in data:
            print(data["error"]["message"])
            return
        else:
            for file in data["children"]:
                item = {
                    "isFolder": "folder" in file,
                    "createTime": 0,
                    "lastOpTime": onedrive.Utils.formatTime(
                        file["lastModifiedDateTime"]
                    ),
                    "parentId": self.md5(file["parentReference"]["path"]),
                    "fileId": self.md5(
                        file["parentReference"]["path"] + "/" + file["name"]
                    ),
                    "filePath": file["parentReference"]["path"].replace(
                        "/drive/root:", user
                    ),
                    "fileName": str(file["name"]),
                    "fileSize": onedrive.Utils.getSize(file["size"]),
                    "fileType": None,
                    "child": [],
                    "user": user,
                }
                isc = True
                if not item["isFolder"]:
                    for x in self.conf["cant_visFile"]:
                        if re.match(x, item["fileName"]) != None:
                            isc = False
                            break
                else:
                    for x in self.conf["cant_enterFolder"]:
                        if re.match(x, item["fileName"]) != None:
                            isc = False
                            break
                if isc == False:
                    continue
                if not item["isFolder"]:
                    item["fileType"] = str(file["name"]).split(".")[-1]
                if item["isFolder"] and file["folder"]["childCount"] > 0:
                    tmp = []
                    item["child"] = tmp
                    self.__proLoad_list(
                        user, tmp, file["parentReference"]["path"] + "/" + file["name"]
                    )
                self.lock.acquire()
                self.real_id[user][item["fileId"]] = (
                    file["parentReference"]["path"] + "/" + file["name"]
                )
                self.lock.release()
                arr.append(item)

    def locate(self, user, path):
        if user not in self.list:
            return False

        now = self.list[user].copy()

        for i in range(1, len(path)):
            nothing = True
            looking = path[i]
            for file in now:
                if looking == file["fileName"]:
                    if i == len(path) - 1:
                        return file
                    if file["isFolder"] and file["child"] != []:
                        nothing = False
                        now = file["child"]
                        break
            if nothing:
                break

        return False

    def locate_id(self, user, fid):
        if user not in self.list:
            return False

        tmp = {0: None}
        self.__proLocate_id(self.list[user].copy(), fid, tmp)

        return tmp[0]

    def __proLocate_id(self, arr, fid, r):
        r[fid] = True
        for file in arr:
            if fid == file["fileId"]:
                r[0] = file
                return
            if r[0] == None and file["fileId"] not in r:
                self.__proLocate_id(file["child"], fid, r)
        return

    def info(self, user, fId, dl=False):
        return self.api[user].get_file_info(self.real_id[user][fId], dl)

    def md5(self, c):
        md5 = hashlib.md5()
        md5.update((c).encode(encoding="utf-8"))
        return md5.hexdigest()
