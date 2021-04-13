# coding=utf-8
import re
import threading
import time
import traceback

from altfe.interface.cloud import interCloud
from app.lib.core.cloud189 import cloud189


@interCloud.bind("cloud_189", "LIB_CORE")
class core_cloud189(interCloud):
    def __init__(self):
        super().__init__()
        self.conf = self.loadConfig(self.getENV("rootPath") + "app/config/cloud189.yml")
        _token = self.loadConfig(self.getENV("rootPath") + "app/lib/core/cloud189/.token.json")
        self.token = _token if _token is not False else {}
        self.listOutdated = 0
        self.api = {}
        self.lock = threading.Lock()
        self.rootPath = [x for x in self.conf["rootPath"].split("/") if x != ""]
        self.auto()

    def auto(self):
        for u in self.conf["accounts"]:
            self.api[u] = cloud189.cloud189(
                self.conf["accounts"][u][0], self.conf["accounts"][u][1]
            )
            tok = self.token[u] if u in self.token else None
            self.token[u] = self.api[u].login(tok)
            self.token[u]["outdated"] = (
                (time.time() + self.conf["sys_tokenExpiredTime"])
                if "outdated" not in self.token[u]
                else self.token[u]["outdated"]
            )
        self.STATIC.file.aout(
            self.getENV("rootPath") + "app/lib/core/cloud189/.token.json", self.token,
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
            print("[Cloud189 Error] " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tim)))
            print(traceback.format_exc())
        t = threading.Timer(self.conf["sys_checkTime"], self.__childth_check)
        t.setDaemon(True)
        t.start()

    def __update_token(self, tim):
        isUp = False
        for u in self.conf["accounts"]:
            if tim > self.token[u]["outdated"]:
                tmp = self.api[u].login(self.token[u])
                tmp["outdated"] = time.time() + self.conf["sys_tokenExpiredTime"]
                self.lock.acquire()
                self.token[u] = tmp
                self.lock.release()
                isUp = True
        if isUp:
            self.STATIC.file.aout(
                self.getENV("rootPath") + "app/lib/core/cloud189/.token.json", self.token,
            )

    def load_list(self):
        for user in self.conf["accounts"].copy():
            self.inCheck = True
            self.lock.acquire()
            self.dirPassword[user] = {}
            self.lock.release()
            tmp = []
            try:
                self.__proLoad_list(user, tmp, -11, str(user) + "/", 0)
            except Exception as e:
                self.STATIC.localMsger.error(e)
            else:
                self.lock.acquire()
                self.list[user] = tuple(tmp)
                self.lock.release()
                print(f"[Cloud189] {user} list updated at " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            self.inCheck = False
        self.listOutdated = time.time() + self.conf["sys_dataExpiredTime"]
        return True

    def __proLoad_list(self, user=None, arr=[], fileId=-11, struri="", rootIndex=0):
        data = self.api[user].get_files(fileId)
        password = None
        for file in data:
            if "._.jl" in file["fileName"]:
                password = file["fileName"][:-5]
                break
        for file in data:
            # 进入根目录
            if len(self.rootPath) != 0 and rootIndex <= len(self.rootPath) - 1:
                if file["isFolder"] and file["fileName"] == self.rootPath[rootIndex]:
                    self.__proLoad_list(
                        user, arr, file["fileId"], struri + file["fileName"] + "/", rootIndex + 1
                    )
                continue
            isPass = True
            if not file["isFolder"]:
                for x in self.conf["cant_visFile"]:
                    if re.match(x, file["fileName"]) != None:
                        isPass = False
                        break
            else:
                for x in self.conf["cant_enterFolder"]:
                    if re.match(x, file["fileName"]) != None:
                        isPass = False
                        break
            if isPass is False:
                continue
            item = {
                "isFolder": file["isFolder"],
                "createTime": file["createTime"],
                "lastOpTime": file["lastOpTime"],
                "parentId": str(file["parentId"]),
                "fileId": str(file["fileId"]),
                "filePath": struri,
                "fileName": str(file["fileName"]),
                "fileSize": 0,
                "fileType": None,
                "child": [],
                "user": user,
                "isSecret": False
            }
            if not file["isFolder"]:
                item["fileSize"] = self.api[user].get_file_size_str(file["fileSize"])
                item["fileType"] = file["fileType"]
            if file["isFolder"]:
                tmp = []
                item["child"] = tmp
                rep = self.__proLoad_list(
                    user, tmp, file["fileId"], struri + file["fileName"] + "/", rootIndex + 1
                )
                if type(rep) == str:
                    self.lock.acquire()
                    self.dirPassword[user][item["fileId"]] = rep
                    item["isSecret"] = True
                    self.lock.release()
            arr.append(item)
        return password

    def info(self, user, fId, dl=False):
        if not user in self.conf["accounts"]:
            return False

        try:
            return self.api[user].get_file_info(fId, dl)
        except:
            self.api[user].login()

        return self.api[user].get_file_info(fId, dl)
