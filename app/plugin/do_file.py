# coding=utf-8
# pylint: disable=relative-beyond-top-level
from ..platform import CMDProcessor
from flask import redirect, jsonify, request
import time
import re


@CMDProcessor.plugin_register("file")
class do_file(object):
    def __init__(self, MOD):
        self.MOD = MOD

    def pRun(self, cmd):
        try:
            argv = self.MOD.args.gets(["id=None"])
        except:
            return jsonify({"code": 0, "msg": "missing parameters"}), 400

        filePath = [x for x in cmd[4:].split("/") if x != ""]
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

        # 读取缓存
        key = argv["id"] if argv["id"] != "None" else full
        _link = [self.MOD.cache.get(user + "_" + key), self.MOD.cache.get(user + "_" + key, "visnum")]
        if _link[0] != None and _link[1] != None:
            if _link[1] <= api.conf["sys_dl_urlExpiredNum"]:
                return redirect(_link[0])
            else:
                self.MOD.cache.delete(user + "_" + key)

        # 检查权限与确定唯一 id
        if argv["id"] != "None":
            fId = argv["id"]
            # 已有 id，但需要确定是否在文件列表中（是否可访问）
            if not api.locate_id(user, fId):
                return "404 Not Found.", 404
        else:
            # 已有文件在文件列表中的路径，需要确定唯一 id
            file = api.locate(user, filePath)
            if not file:
                return "404 Not Found.", 404
            fId = file["fileId"]

        # 获取下载链接
        url = api.info(user, fId, True)

        if url:
            self.MOD.cache.set(user + "_" + key, url, api.conf["sys_dl_urlExpiredTime"])
            return redirect(url)
        else:
            return "Not a File.", 400
