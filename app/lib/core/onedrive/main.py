# coding=utf-8
import json
import threading
import time
import traceback
from concurrent.futures import as_completed
from urllib import parse

from altfe.interface.cloud import interCloud
from app.lib.core.onedrive import onedrive


@interCloud.bind("cloud_onedrive", "LIB_CORE")
class core_onedrive(interCloud):
    def __init__(self):
        super().__init__()
        self.conf = self.loadConfig(self.getENV("rootPath") + "app/config/onedrive.yml")
        _token = self.loadConfig(self.getENV("rootPath") + "app/lib/core/onedrive/.token.json")
        self.token = _token if _token is not False else {}
        self.accessToken = {}
        self.api = {}
        self.listOutdated = 0
        self.realID = {}
        self.lock = threading.Lock()
        self.auto()

    def auto(self):
        for u in self.conf["accounts"]:
            self.realID[u] = {}
            is_cn = self.conf["accounts"][u][0]
            ms = onedrive.OneDrive("", IS_CN=is_cn)
            refreshToken = self.token[u] if u in self.token else None
            if refreshToken is None:
                print(f"[{u}] 进入以下网址以获取 Code 字段")
                print(
                    f"{onedrive.oauthHost[is_cn]}/common/oauth2/v2.0/authorize?client_id={onedrive.clientId[is_cn]}&response_type=code&redirect_uri={onedrive.redirectHost[is_cn]}&response_mode=query&scope=offline_access%20User.Read%20Files.ReadWrite.All"
                )
                print("Code 为跳转后 URL 的 ?code= 到 &session_state 的中间部分")
                code = str(input("Code: ").strip())
                ms.getToken(code)
                refreshToken = ms.refresh_token
                self.token[u] = refreshToken
            self.api[u] = onedrive.OneDrive(
                refreshToken,
                self.conf["rootPath"],
                onedrive.redirectHost[is_cn],
                is_cn,
            )
            self.accessToken[u] = self.api[u].getAccessToken()
            self.accessToken[u]["outdated"] = time.time() + self.accessToken[u]["expires_in"] - 60
        self.STATIC.file.aout(
            self.getENV("rootPath") + "app/lib/core/onedrive/.token.json", self.token
        )
        t = threading.Timer(0, self.__childth_check)
        t.setDaemon(True)
        t.start()

    def __childth_check(self):
        tim = time.time()
        try:
            self.__update_token(tim)
            if tim > self.listOutdated:
                self.load_list()
        except:
            print("[OneDrive Error] " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tim)))
            print(traceback.format_exc())
        t = threading.Timer(self.conf["sys_checkTime"], self.__childth_check)
        t.setDaemon(True)
        t.start()

    def __update_token(self, tim):
        isUp = False
        for u in self.conf["accounts"]:
            if tim > self.accessToken[u]["outdated"]:
                tmp = self.api[u].getAccessToken(self.token[u])
                tmp["outdated"] = time.time() + tmp["expires_in"] - 60
                self.lock.acquire()
                self.accessToken[u] = tmp
                self.token[u] = self.accessToken[u]["refresh_token"]
                self.lock.release()
                isUp = True
        if isUp:
            self.STATIC.file.aout(
                self.getENV("rootPath") + "app/lib/core/onedrive/.token.json", self.token
            )

    def load_list(self):
        for u in self.conf["accounts"].copy():
            self.inCheck = True
            tmp = []
            try:
                self.__proLoad_list(u, tmp)
                psws = self.STATIC.util.process_addPassword(tmp)
            except Exception as e:
                self.STATIC.localMsger.error(e)
            else:
                self.lock.acquire()
                self.dirPassword[u] = psws
                self.list[u] = tuple(tmp)
                self.lock.release()
                print(f"[OneDrive] {u} list updated at " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            self.inCheck = False
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
            self.STATIC.localMsger.error(data["error"]["message"])
            return
        status = []
        for file in data["children"]:
            # 过滤排除的文件夹/文件
            if self.STATIC.util.isNeedLoad("folder" in file, str(file["name"]), self.conf):
                continue
            # 项
            item = {
                "isFolder": "folder" in file,
                "createTime": 0,
                "lastOpTime": onedrive.Utils.formatTime(
                    file["lastModifiedDateTime"]
                ),
                "parentId": self.STATIC.util.md5(file["parentReference"]["path"]),
                "fileId": self.STATIC.util.md5(
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
                "isSecret": False
            }
            if not item["isFolder"]:
                item["fileType"] = str(file["name"]).split(".")[-1]
            if item["isFolder"] and file["folder"]["childCount"] > 0:
                status.append(self.COMMON.thread.plz().submit(self.__proLoad_list, *(
                    user, item["child"], file["parentReference"]["path"] + "/" + file["name"])))
            self.lock.acquire()
            self.realID[user][item["fileId"]] = (
                    file["parentReference"]["path"] + "/" + file["name"]
            )
            self.lock.release()
            arr.append(item)
        # 阻塞多线程获取文件夹内容
        for x in as_completed(status):
            pass

    def info(self, user, fid, dl=False):
        return self.api[user].get_file_info(self.realID[user][fid], dl)
