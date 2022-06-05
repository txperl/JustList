import threading
import time
from concurrent.futures import as_completed

from altfe.interface.cloud import interCloud
from app.lib.core.onedrive.onedrive import OneDrive


@interCloud.bind("cloud_onedrive", "LIB_CORE")
class CoreOneDrive(interCloud):
    def __init__(self):
        super().__init__()
        self.conf = self.INS.conf.dict("onedrive")
        self.listOutdated = 0
        self.realID = {}
        self.auto()

    def auto(self):
        if self.conf["accounts"] is None:
            return
        self.is_on = True
        _token = self.loadConfig(self.getENV("rootPathFrozen") + "app/config/.token/onedrive.json", default={})
        for u in self.conf["accounts"]:
            class_one = OneDrive(is_cn=int(self.conf["accounts"][u]))
            func_body = {}
            if _token.get(u) is None or _token.get(u).get("refresh") is None:
                print(f"[OneDrive] {u} 请进入以下地址获取 Code 以登录")
                print(
                    f"{class_one.oauth_host}/common/oauth2/v2.0/authorize?client_id={class_one.client_id}&response_type=code&redirect_uri={class_one.redirect_host}&response_mode=query&scope=offline_access%20User.Read%20Files.ReadWrite.All")
                print("Code 为跳转后网址的 ?code= 到 &session_state 的中间部分")
                code = str(input("Code: ").strip())
                func_body.update({"code": code})
            else:
                func_body.update({"refresh_token": _token.get(u).get("refresh")})
            if class_one.do_refresh_token(**func_body):
                self.api[u] = class_one
                self.realID[u] = {}
                self.__save_token()
            else:
                print(f"[OneDrive] {u} 登录失败")
        t = threading.Timer(0, self.__childth_check)
        t.setDaemon(True)
        t.start()

    def __childth_check(self):
        while True:
            tim = time.time()
            isUP = False
            for u in self.api:
                if tim > self.api[u].get_token("expire") - 600:
                    try:
                        self.api[u].do_refresh_token()
                    except Exception as e:
                        self.STATIC.localMsger.error(e)
                    else:
                        isUP = True
            if isUP:
                self.__save_token()
            if tim > self.listOutdated:
                self.load_list()
            time.sleep(self.conf["sys_checkTime"])

    def __save_token(self):
        r = {}
        for u in self.api:
            r[u] = self.api[u].get_token()
        self.STATIC.file.aout(self.getENV("rootPathFrozen") + "app/config/.token/onedrive.json", r)

    def load_list(self):
        if self.is_on is False:
            return False
        for u in self.api:
            self.inCheck = True
            tmp = []
            try:
                self.__proLoad_list(u, tmp)
                psws = interCloud.process_add_password(tmp)
            except Exception as e:
                self.STATIC.localMsger.error(e)
            else:
                self.dirPassword[u] = psws
                self.list[u] = tuple(tmp)
                self.listOutdated = time.time() + self.conf["sys_dataExpiredTime"]
                print(f"[OneDrive] {u} list updated at " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            self.inCheck = False
        return True

    def __proLoad_list(self, user, arr, path=None):
        if path is None:
            path = self.conf["rootPath"]
        data = self.api[user].get_list(path)
        if "children" not in data:
            return []
        status = []
        for file in data["children"]:
            # 过滤排除的文件夹/文件
            if self.STATIC.util.isNeedLoad("folder" in file, str(file["name"]), self.conf):
                continue
            # 项
            item = {
                "isFolder": "folder" in file,
                "createTime": 0,
                "lastOpTime": self.STATIC.util.format_time(
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
                "fileSize": self.STATIC.util.format_size(file["size"]),
                "fileType": None,
                "child": [],
                "user": user,
                "isSecret": False,
                "driveName": "onedrive"
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
            return self.api[user].get_download_url(self.realID[user][fid])
        except Exception as e:
            self.STATIC.localMsger.error(e)
            self.STATIC.localMsger.green(f"[OneDrive] {user} try to login")
            try:
                self.api[user].do_refresh_token()
                return self.api[user].get_download_url(self.realID[user][fid])
            except Exception as ee:
                self.STATIC.localMsger.error(ee)
        return False
