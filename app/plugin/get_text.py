# coding=utf-8
# pylint: disable=relative-beyond-top-level
from ..platform import CMDProcessor
from urllib.parse import unquote
from flask import jsonify, request
import requests
import time
import re


@CMDProcessor.plugin_register("api/get/text")
class do_get_text(object):
    def __init__(self, MOD):
        self.MOD = MOD

    def pRun(self, cmd):
        try:
            argv = self.MOD.args.gets(["id=None"])
        except:
            return jsonify({"code": 0, "msg": "missing parameters"}), 400

        filePath = [x for x in cmd[12:].split("/") if x != ""]
        if len(filePath) == 0:
            return jsonify({"code": 0, "msg": "missing parameters"}), 400
        user = filePath[0]
        full = "/".join(filePath)
        api = None

        # 确定具体 api
        for name in dir(self.MOD):
            if "cloud_" in name:
                tmp = getattr(self.MOD, name)
                if user in tmp.list:
                    api = tmp
                    break

        if api == None:
            return jsonify({"code": 0, "msg": "unknown user"}), 400

        # 简单验证 Referrer
        if len(api.conf["only_Referrer"]) != 0:
            isc = False
            for x in api.conf["only_Referrer"]:
                if re.search(x, str(request.referrer)) != None:
                    isc = True
                    break
            if isc == False:
                return "Request Forbidden.", 403

        # 如果有线程正在更新，则阻塞
        # trysum = 0
        # while True:
        #     if api.inCheck == False or trysum > 10:
        #         break
        #     trysum += 1
        #     time.sleep(0.5)

        finalUrl = None

        # 读取缓存
        # key = argv["id"] if argv["id"] != "None" else full
        # _link = [self.MOD.cache.get(user + "_" + key), self.MOD.cache.get(user + "_" + key, "visnum")]
        # if _link[0] != None and _link[1] != None:
        #     if _link[1] <= api.conf["sys_dl_urlExpiredNum"]:
        #         finalUrl = _link[0]
        #     else:
        #         self.MOD.cache.delete(user + "_" + key)

        url = finalUrl

        if url == None:
            # 检查权限与确定唯一 id
            if argv["id"] != "None":
                fId = argv["id"]
                # 已有 id，但需要确定是否在文件列表中（是否可访问）
                file = api.locate_id(user, fId)
                if not file or (file["fileType"] != "txt" and file["fileType"] != "md"):
                    return "404 Not Found.", 404
            else:
                # 已有文件在文件列表中的路径，需要确定唯一 id
                file = api.locate(user, filePath)
                if not file or (file["fileType"] != "txt" and file["fileType"] != "md"):
                    return "404 Not Found.", 404
                fId = file["fileId"]
            # 获取下载链接
            url = api.info(user, fId, True)

        if url:
            try:
                r = requests.get(url, timeout=10).text
                if "此下载链接已过有效期" in r:
                    print("Failed to Get. Try again.")
                    r = requests.get(url, timeout=10).text
                    if "此下载链接已过有效期" in r:
                        return "Failed to Get."
                return r
            except:
                return "Failed."
        else:
            return "Not a File."
