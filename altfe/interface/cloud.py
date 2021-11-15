import threading

import bcrypt

from altfe.interface.root import interRoot


class interCloud(interRoot):
    """
    网盘核心接口类。
    """

    def __init__(self):
        self.list = {}
        self.dirPassword = {}
        self.lock = threading.Lock()
        self.inCheck = False

    def load_list(self):
        return True

    def locate_all(self, user, password=()):
        return self.filter_verify_password(self.list[user], self.dirPassword[user], password)

    def locate(self, user, path, password=()):
        now = self.locate_all(user, password)
        for i in range(1, len(path)):
            nothing = True
            looking = path[i]
            for file in now:
                if looking == file["fileName"]:
                    if i == len(path) - 1:
                        return [file]
                    if file["isFolder"] and file["child"] != []:
                        nothing = False
                        now = file["child"]
                        break
            if nothing:
                break
        return []

    def locate_id(self, user, fid, password=()):
        def process_locate_by_id(arr, fid, r):
            r[fid] = True
            for file in arr:
                if fid == file["fileId"]:
                    r[0] = [file]
                    return
                if len(r[0]) == 0 and file["fileId"] not in r:
                    process_locate_by_id(file["child"], fid, r)
            return

        li = self.locate_all(user, password)
        if fid == -11:
            return li
        tmp = {0: []}
        process_locate_by_id(li, fid, tmp)
        return tmp[0]

    def info(self, user, fid, dl=False):
        return False

    @classmethod
    def process_add_password(cls, arr, passwords={}):
        """
        查找用户列表文件中的加密文件夹。
        :param arr: 用户网盘列表
        :param passwords: 密码集
        :return: dict@{fileId: password}
        """
        for file in arr:
            if file["isFolder"]:
                for i in range(len(file["child"])):
                    child = file["child"][i]
                    if "._.jl" in child["fileName"]:
                        passwords[file["fileId"]] = child["fileName"][:-5]
                        file["isSecret"] = True
                        del file["child"][i]
                        break
                cls.process_add_password(file["child"], passwords)
        return passwords

    @classmethod
    def filter_verify_password(cls, li, allPassword={}, password=(), index=0):
        """
        读取密码匹配的目录。
        :param li: 所有文件目录
        :param allPassword: 所有密码
        :param password: 密码序列
        :param index: 密码序列索引
        :return: 最终筛选后的目录
        """
        r = []
        for i in range(len(li)):
            file = li[i].copy()
            if file["isSecret"]:
                if len(password) > index and interCloud.verify_bcrypt_password(password[index],
                                                                               allPassword[file["fileId"]]):
                    index += 1
                else:
                    if file["isFolder"]:
                        file["child"] = []
                        r.append(file)
                    continue
            if file["isFolder"]:
                file["child"] = cls.filter_verify_password(file["child"], allPassword, password, index)
            r.append(file)
        return r

    @staticmethod
    def verify_bcrypt_password(hashed, password):
        """
        验证密码明文与哈希值是否匹配。
        :param hashed: 哈希值
        :param password: 密码明文
        :return: true or false
        """
        try:
            return bcrypt.checkpw(str(password).encode("utf8"), str(hashed).encode("utf8"))
        except:
            return False
