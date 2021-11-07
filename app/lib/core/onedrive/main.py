# coding=utf-8
import json
import threading
import time
from concurrent.futures import as_completed
from urllib import parse

from altfe.interface.cloud import interCloud
from app.lib.core.onedrive import onedrive


@interCloud.bind("cloud_onedrive", "LIB_CORE")
class core_onedrive(interCloud):
    def __init__(self):
        super().__init__()
        self.conf = self.loadConfig(self.getENV("rootPathFrozen") + "app/config/onedrive.yml")
        self.api = {}
        self.listOutdated = 0
        self.realID = {}
        self.lock = threading.Lock()
        self.auto()

    def auto(self):
        if self.conf["accounts"] is None:
            return
        _token = self.loadConfig(self.getENV("rootPathFrozen") + "app/config/.token/onedrive.json", default={})
        for u in self.conf["accounts"]:
            if u not in _token:
                _token[u] = None
            self.realID[u] = {}
            is_cn = self.conf["accounts"][u]
            self.api[u] = onedrive.OneDrive(_token[u],
                                            self.conf["rootPath"],
                                            onedrive.redirectHost[is_cn],
                                            is_cn)
            if _token[u] is None:
                print(f"[OneDrive@{u}] 进入以下网址获取 Code 字段以登录")
                print(
                    f"{onedrive.oauthHost[is_cn]}/common/oauth2/v2.0/authorize?client_id={onedrive.clientId[is_cn]}&response_type=code&redirect_uri={onedrive.redirectHost[is_cn]}&response_mode=query&scope=offline_access%20User.Read%20Files.ReadWrite.All"
                )
                print("Code 为跳转后 URL 的 ?code= 到 &session_state 的中间部分")
                code = str(input("Code: ").strip())
                self.api[u].getToken(code)
            else:
                self.api[u].getAccessToken()
        self.__save_refreshToken()
        t = threading.Timer(0, self.__childth_check)
        t.setDaemon(True)
        t.start()

    def __childth_check(self):
        while True:
            tim = time.time()
            try:
                isUp = False
                for u in self.api:
                    if tim > self.api[u].outdated - 600:
                        self.api[u].getAccessToken()
                        isUp = True
                if isUp:
                    self.__save_refreshToken()
                if tim > self.listOutdated:
                    self.load_list()
            except Exception as e:
                self.STATIC.localMsger.error(e)
            time.sleep(self.conf["sys_checkTime"])

    def __save_refreshToken(self):
        r = {}
        for u in self.api:
            r[u] = self.api[u].refresh_token
        self.STATIC.file.aout(self.getENV("rootPathFrozen") + "app/config/.token/onedrive.json", r)

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
            elif file["folder"]["childCount"] > 0:
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
        try:
            return self.api[user].get_file_info(self.realID[user][fid], dl)
        except Exception as e:
            self.STATIC.localMsger.error(e)
            return False
