from altfe.interface.root import interRoot


@interRoot.bind("api/get/list/", "PLUGIN")
class get_list(interRoot):
    def run(self, cmd):
        try:
            argv = self.STATIC.arg.gets(["id={_none}", "password={_blank}"], "POST")
        except:
            return {"code": 0, "msg": "bad request or missing parameters"}

        filePath = [x for x in cmd.split("/") if x != ""]
        numOfpath = len(filePath)
        apis = []
        api = None

        # 列出所有 api
        for name in dir(self.CORE):
            if "cloud_" in name:
                apis.append(getattr(self.CORE, name))

        # 返回全部列表
        if numOfpath == 0:
            r = {}
            for x in apis:
                for u in x.list:
                    r[u] = x.locate_all(u)
            return {"code": 1, "msg": r, }

        user = filePath[0]
        # 确定具体 api
        for func in apis:
            if user in func.list:
                api = func
                break

        if api is None:
            return {"code": 0, "msg": "unknown user"}

        if numOfpath == 1:
            if argv["id"] is not None:
                fId = argv["id"]
                r = api.locate_id(user, fId, [x for x in argv["password"].split("._.") if x != ""])
            else:
                r = {}
                for u in api.list:
                    r[u] = api.locate_all(u)
        else:
            r = api.locate(user, filePath, [x for x in argv["password"].split("._.") if x != ""])

        if r:
            return {"code": 1, "msg": r, }

        return {"code": 404, "msg": "404 Not Found."}
