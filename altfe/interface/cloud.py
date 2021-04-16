from altfe.interface.root import interRoot


class interCloud(interRoot):
    """
    网盘核心接口类。
    """

    def __init__(self):
        self.list = {}
        self.dirPassword = {}
        self.inCheck = False

    def load_list(self):
        return []

    def locateAll(self, user, password=()):
        return self.STATIC.util.filterVerifyPassword(self.list[user], self.dirPassword[user], password)

    def locate(self, user, path, password=()):
        return self.STATIC.util.locateByPath(self.locateAll(user, password), path)

    def locate_id(self, user, fid, password=()):
        li = self.locateAll(user, password)
        if fid == -11:
            return li
        tmp = {0: []}
        self.STATIC.util.process_locateByID(li, fid, tmp)
        return tmp[0]

    def info(self, user, fid, dl=False):
        return False
