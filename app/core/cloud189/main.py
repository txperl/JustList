# coding=utf-8
# pylint: disable=relative-beyond-top-level,unused-wildcard-import
from ...platform import CMDProcessor
from ..file import main as ifile
from . import cloud189
import threading
import json
import time
import sys
import re
import os


@CMDProcessor.core_register_auto(
    "cloud_189", {"config": "{ROOTPATH}app/core/cloud189/config.json"}
)
class core_module_cloud189(object):
    def __init__(self, info=None):
        self.ENVORON = info["ENVIRON"]
        self.conf = info["config"]
        self.token = {}
        self.listOutdated = 0
        self.api = {}
        self.list = {}
        self.inCheck = False
        self.lock = threading.Lock()

    def auto(self):
        for u in self.conf["accounts"]:
            self.api[u] = cloud189.cloud189(
                self.conf["accounts"][u][0], self.conf["accounts"][u][1]
            )
            tok = (
                self.conf["accounts"][u][2]
                if self.conf["accounts"][u][2] != {}
                else None
            )
            self.token[u] = self.api[u].login(tok)
            self.token[u]["outdated"] = (
                (time.time() + self.conf["sys_cookieExpiredTime"])
                if "outdated" not in self.token[u]
                else self.token[u]["outdated"]
            )
            self.conf["accounts"][u][2] = self.token[u]
        ifile.io.aout(
            self.ENVORON["ROOTPATH"] + "app/core/cloud189/config.json", self.conf,
        )
        t = threading.Timer(0, self.__childth_check)
        t.setDaemon(True)
        t.start()
        return self

    def load_list(self):
        for k in self.conf["accounts"].copy():
            tmp = []
            self.__proLoad_list(k, tmp, -11, str(k) + "/")
            self.lock.acquire()
            self.inCheck = True
            self.list[k] = tmp
            self.inCheck = False
            self.lock.release()
            print(f"[cloud189] {k} list updated")
        self.listOutdated = time.time() + self.conf["sys_dataExpiredTime"]
        return True

    def __proLoad_list(self, user=None, arr=[], fileId=-11, struri=""):
        data = self.api[user].get_files(fileId)
        for file in data:
            isc = True
            if not file["isFolder"]:
                for x in self.conf["cant_visFile"]:
                    if re.match(x, file["fileName"]) != None:
                        isc = False
                        break
            else:
                for x in self.conf["cant_enterFolder"]:
                    if re.match(x, file["fileName"]) != None:
                        isc = False
                        break
            if isc == False:
                continue

            item = {
                "isFolder": file["isFolder"],
                "createTime": file["createTime"],
                "lastOpTime": file["lastOpTime"],
                "parentId": file["parentId"],
                "fileId": file["fileId"],
                "filePath": struri,
                "fileName": str(file["fileName"]),
                "fileSize": 0,
                "fileType": None,
                "child": [],
                "user": user,
            }
            if not file["isFolder"]:
                item["fileSize"] = self.api[user].get_file_size_str(file["fileSize"])
                item["fileType"] = file["fileType"]
            if file["isFolder"]:
                tmp = []
                item["child"] = tmp
                self.__proLoad_list(
                    user, tmp, file["fileId"], struri + file["fileName"] + "/"
                )
            arr.append(item)
        return True

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
        if fid == -11:
            return self.list[user]

        tmp = {0: None}
        self.__proLocate_id(self.list[user].copy(), fid, tmp)

        return tmp[0]

    def __proLocate_id(self, arr, fid, r):
        r[str(fid)] = True
        for file in arr:
            if fid == file["fileId"]:
                r[0] = file
                return
            if r[0] == None and str(file["fileId"]) not in r:
                self.__proLocate_id(file["child"], fid, r)
        return

    def info(self, user, fId, dl=False):
        if not user in self.conf["accounts"]:
            return False

        try:
            return self.api[user].get_file_info(fId, dl)
        except:
            self.api[user].login()

        return self.api[user].get_file_info(fId, dl)

    def __childth_check(self):
        tim = time.time()
        print(
            "[cloud189] checking at %s"
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
        for u in self.conf["accounts"].copy():
            if tim > self.token[u]["outdated"]:
                tmp = self.api[u].login(self.token[u])
                self.lock.acquire()
                self.token[u] = tmp
                self.token[u]["outdated"] = (
                    time.time() + self.conf["sys_cookieExpiredTime"]
                )
                self.conf["accounts"][u][2] = self.token[u]
                self.lock.release()
                isUp = True
        if isUp:
            ifile.io.aout(
                self.ENVORON["ROOTPATH"] + "app/core/cloud189/config.json", self.conf,
            )
