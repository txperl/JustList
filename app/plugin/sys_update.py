import traceback

from altfe.interface.root import interRoot


@interRoot.bind("sys/update/xxxiiixxx", "PLUGIN")
class sys_update(interRoot):
    def run(self, cmd):
        apis = []
        for name in dir(self.CORE):
            if "cloud_" in name:
                apis.append(getattr(self.CORE, name))
        error = 0
        for api in apis:
            try:
                api.load_list()
            except Exception:
                self.STATIC.localMsger.error(traceback.format_exc())
                error += 1
        if error > 0:
            return {"code": 0, "msg": f"errors in {str(error)}/{str(len(apis))}"}
        return {"code": 1, "msg": "done"}
