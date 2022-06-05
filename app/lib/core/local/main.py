import os
import threading
import time

from flask import send_file

from altfe.interface.cloud import interCloud


@interCloud.bind("cloud_local", "LIB_CORE")
class CoreLocal(interCloud):
    def __init__(self):
        super().__init__()
        self.conf = self.INS.conf.dict("local")
        self.conf.update({"sys_dl_urlExpiredTime": -1, "sys_dl_urlExpiredNum": -1})
        self.accounts = self.conf["accounts"]
        self.listOutdated = 0
        self.realID = {}
        self.auto()

    def auto(self):
        if self.accounts is None:
            return
        self.is_on = True
        for user in self.accounts.copy():
            self.realID[user] = {}
            if self.accounts[user][-1] != "/":
                self.accounts[user] += "/"
        t = threading.Timer(0, self.__childth_check)
        t.setDaemon(True)
        t.start()

    def __childth_check(self):
        while True:
            try:
                self.load_list()
            except Exception as e:
                self.STATIC.localMsger.error(e)
            time.sleep(self.conf["sys_dataExpiredTime"])

    def load_list(self):
        if self.is_on is False:
            return False
        for u in self.accounts:
            self.inCheck = True
            try:
                tmp = self.__proLoad_list(u, self.accounts[u])
                psws = interCloud.process_add_password(tmp)
            except Exception as e:
                self.STATIC.localMsger.error(e)
            else:
                self.dirPassword[u] = psws
                self.list[u] = tuple(tmp)
                self.listOutdated = time.time() + self.conf["sys_dataExpiredTime"]
                print(f"[Local] {u} list updated at " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            self.inCheck = False
        return True

    def __proLoad_list(self, user, path):
        r = []
        data = os.listdir(path)
        for fileName in data:
            filePath = path + fileName
            # 过滤排除的文件夹/文件
            if self.STATIC.util.isNeedLoad(os.path.isdir(filePath), str(fileName), self.conf):
                continue
            item = {
                "isFolder": os.path.isdir(filePath),
                "createTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(filePath))),
                "lastOpTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(filePath))),
                "parentId": self.STATIC.util.md5(path),
                "fileId": self.STATIC.util.md5(filePath),
                "filePath": path,
                "fileName": str(fileName),
                "fileSize": self.STATIC.util.format_size(os.path.getsize(filePath)),
                "fileType": None,
                "child": [],
                "user": user,
                "isSecret": False,
                "driveName": "local"
            }
            if not item["isFolder"]:
                item["fileType"] = item["fileName"].split(".")[-1]
            else:
                item["child"] = self.__proLoad_list(user, filePath + "/")
            self.lock.acquire()
            self.realID[user][item["fileId"]] = filePath
            self.lock.release()
            r.append(item)
        return r

    def info(self, user, fid, dl=False):
        try:
            return send_file(self.realID[user][fid], as_attachment=True)
        except Exception as e:
            self.STATIC.localMsger.error(e)
            return False
