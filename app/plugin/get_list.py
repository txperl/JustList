# coding=utf-8
# pylint: disable=relative-beyond-top-level
from ..platform import CMDProcessor
from flask import jsonify
import time


@CMDProcessor.plugin_register("api/get/list")
class get_list(object):
    def __init__(self, MOD):
        self.MOD = MOD

    def pRun(self, cmd):
        try:
            argv = self.MOD.args.gets(["id=None"])
        except:
            return jsonify({"code": 0, "msg": "missing parameters"}), 400

        filePath = [x for x in cmd[12:].split("/") if x != ""]
        numOfpath = len(filePath)
        apis = []
        api = None

        # 列出所有 api
        for name in dir(self.MOD):
            if "cloud_" in name:
                apis.append(getattr(self.MOD, name))

        # 返回全部列表
        if numOfpath == 0:
            # 如果有线程正在更新，则阻塞
            # trysum = 0
            # while True:
            #     status = [x.inCheck for x in apis]
            #     if not True in status or trysum > 10:
            #         break
            #     trysum += 1
            #     time.sleep(0.5)
            r = {}
            for x in apis:
                for u in x.list:
                    r[u] = x.list[u]
            return {
                "code": 1,
                "msg": r,
            }

        user = filePath[0]
        # 确定具体 api
        for func in apis:
            if user in func.list:
                api = func
                break

        if api == None:
            return jsonify({"code": 0, "msg": "unknown user"}), 400

        # 如果线程正在更新，则阻塞
        # trysum = 0
        # while True:
        #     if api.inCheck == False or trysum > 10:
        #         break
        #     trysum += 1
        #     time.sleep(0.5)

        if numOfpath == 1:
            r = {}
            for u in api.list:
                r[u] = api.list[u]
            return {
                "code": 1,
                "msg": r,
            }
        else:
            if argv["id"] != "None":
                fId = argv["id"]
                file = api.locate_id(user, fId)
            else:
                file = api.locate(user, filePath)
            if file:
                return {
                    "code": 1,
                    "msg": file,
                }

        return "404 Not Found.", 404
