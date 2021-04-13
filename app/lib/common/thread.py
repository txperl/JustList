from concurrent.futures.thread import ThreadPoolExecutor

from altfe.interface.root import interRoot


@interRoot.bind("thread", "LIB_COMMON")
class common_pool(object):
    pool = ThreadPoolExecutor(max_workers=8)

    @classmethod
    def plz(cls):
        return cls.pool
