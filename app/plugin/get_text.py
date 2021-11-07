# coding=utf-8

import requests

from altfe.interface.root import interRoot


@interRoot.bind("api/get/text/", "PLUGIN")
class do_get_text(interRoot):
    def run(self, cmd):
        try:
            argv = self.STATIC.arg.gets(["id={_none}", "password={_blank}"], "POST")
        except:
            return {"code": 0, "msg": "bad request or missing parameters"}

        filePath = [x for x in cmd.split("/") if x != ""]
        if len(filePath) == 0:
            return {"code": 0, "msg": "missing parameters"}
        user = filePath[0]
        full = "/".join(filePath)
        api = None

        # 确定具体 api
        for name in dir(self.CORE):
            if "cloud_" in name:
                tmp = getattr(self.CORE, name)
                if user in tmp.list:
                    api = tmp
                    break

        if api is None:
            return {"code": 0, "msg": "unknown user"}

        finalUrl = None

        # 读取缓存
        key = self.STATIC.util.md5(full + str(argv["id"]) + str(argv["password"]))
        _link = [self.INS.cache.get(key), self.INS.cache.get(key, "visnum"), self.INS.cache.get(key + "_psw")]
        if _link[0] is not None:
            if _link[1] <= api.conf["sys_dl_urlExpiredNum"]:
                if _link[2] == argv["password"]:
                    finalUrl = _link[0]

        url = finalUrl

        if url is None:
            # 检查权限与确定唯一 id
            if argv["id"] is not None:
                fId = argv["id"]
                # 已有 id，但需要确定是否在文件列表中（是否可访问）
                file = api.locate_id(user, fId, [x for x in argv["password"].split("._.") if x != ""])
                if not file or (file[0]["fileType"] != "txt" and file[0]["fileType"] != "md"):
                    return "404 Not Found.", 404
            else:
                # 已有文件在文件列表中的路径，需要确定唯一 id
                file = api.locate(user, filePath, [x for x in argv["password"].split("._.") if x != ""])
                if not file or (file[0]["fileType"] != "txt" and file[0]["fileType"] != "md"):
                    return "404 Not Found.", 404
                fId = file[0]["fileId"]

            # 获取下载链接
            if type(api).__name__ == "core_local":
                return api.info(user, fId, False)
            else:
                url = api.info(user, fId, True)

        if url:
            try:
                r = requests.get(url, timeout=10).text
                if "此下载链接已过有效期" in r:
                    return "Failed to Get.", 500
                return r
            except:
                return "Failed.", 500
        else:
            return "Have no File.", 400
