# coding=utf-8
# pylint: disable=relative-beyond-top-level
from ..platform import CMDProcessor


@CMDProcessor.plugin_register("sys/update/xxxiiixxx")
class sys_update(object):
    def __init__(self, MOD):
        self.MOD = MOD

    def pRun(self, cmd):
        apis = []
        # 列出所有 api
        for name in dir(self.MOD):
            if "cloud_" in name:
                apis.append(getattr(self.MOD, name))

        try:
            for api in apis:
                api.load_list()
        except:
            return {"code": 0, "msg": "error;"}
        return {"code": 1, "msg": "done"}
