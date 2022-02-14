import os
import threading
import time
from concurrent.futures import as_completed

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
        for u in self.accounts:
            self.inCheck = True
            tmp = []
            try:
                self.__proLoad_list(u, tmp, self.accounts[u])
                psws = interCloud.process_add_password(tmp)
            except Exception as e:
                self.STATIC.localMsger.error(e)
            else:
                self.lock.acquire()
                self.dirPassword[u] = psws
                self.list[u] = tuple(tmp)
                self.lock.release()
                print(f"[Local] {u} list updated at " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            self.inCheck = False
        self.listOutdated = time.time() + self.conf["sys_dataExpiredTime"]
        return True

    def __proLoad_list(self, user, arr, path):
        data = os.listdir(path)
        status = []
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
                "fileSize": self.STATIC.util.pureSize(os.path.getsize(filePath)),
                "fileType": None,
                "child": [],
                "user": user,
                "isSecret": False,
                "driveName": "local"
            }
            if not item["isFolder"]:
                item["fileType"] = item["fileName"].split(".")[-1]
            else:
                status.append(
                    self.COMMON.thread.plz().submit(self.__proLoad_list, *(user, item["child"], filePath + "/")))
            self.lock.acquire()
            self.realID[user][item["fileId"]] = filePath
            self.lock.release()
            arr.append(item)
        # 阻塞多线程获取文件夹内容
        for x in as_completed(status):
            pass

    def info(self, user, fid, dl=False):
        try:
            if dl:
                rep = send_file(self.realID[user][fid], as_attachment=True)
                # rep.headers["content-disposition"] = "attachment; filename=" + self.realID[user][fid].split("/")[-1]
                return rep
            else:
                return self.STATIC.file.ain(self.realID[user][fid])
        except Exception as e:
            self.STATIC.localMsger.error(e)
            return False
