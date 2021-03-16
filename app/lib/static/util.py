import hashlib

import bcrypt

from altfe.interface.root import interRoot


@interRoot.bind("util", "LIB_STATIC")
class static_util(object):
    @classmethod
    def filterVerifyPassword(cls, li, allPassword={}, password=(), index=0):
        r = []
        for i in range(len(li)):
            file = li[i].copy()
            if file["isSecret"]:
                if len(password) > index and cls.verifyBcryptPassword(password[index], allPassword[file["fileId"]]):
                    index += 1
                else:
                    if file["isFolder"]:
                        file["child"] = []
                        r.append(file)
                    continue
            if file["isFolder"]:
                file["child"] = cls.filterVerifyPassword(file["child"], allPassword, password, index)
            r.append(file)
        return r

    @classmethod
    def process_locateByID(cls, arr, fid, r):
        r[fid] = True
        for file in arr:
            if fid == file["fileId"]:
                r[0] = [file]
                return
            if len(r[0]) == 0 and file["fileId"] not in r:
                cls.process_locateByID(file["child"], fid, r)
        return

    @staticmethod
    def locateByPath(now, path):
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

    @staticmethod
    def verifyBcryptPassword(hashed, password):
        try:
            return bcrypt.checkpw(str(password).encode('utf8'), str(hashed).encode('utf8'))
        except:
            return False

    @staticmethod
    def md5(c):
        md5 = hashlib.md5()
        md5.update((c).encode(encoding="utf-8"))
        return md5.hexdigest()
