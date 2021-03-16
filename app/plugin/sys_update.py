# coding=utf-8
from altfe.interface.root import interRoot


@interRoot.bind("sys/update/xxxiiixxx", "PLUGIN")
class sys_update(interRoot):
    def run(self, cmd):
        apis = []
        # 列出所有 api
        for name in dir(self.CORE):
            if "cloud_" in name:
                apis.append(getattr(self.CORE, name))
        try:
            for api in apis:
                api.load_list()
        except:
            return {"code": 0, "msg": "error"}
        return {"code": 1, "msg": "done"}
