from cache.connection import HarvestCacheConnection
from logging import getLogger

logger = getLogger('harvest')


class HarvestCacheHeartBeatThread:
    def __init__(self, cache: HarvestCacheConnection, version: str):
        self._version = version
        self._cache = cache

        from threading import Thread
        self.thread = Thread(target=self._run, name='cache_heartbeat', daemon=True)

        self.thread.start()

    def _run(self):
        logger.info('heartbeat: started')

        import platform
        from socket import getfqdn, gethostbyname
        from datetime import datetime, timezone
        from plugins import PluginRegistry

        start_datetime = datetime.now(tz=timezone.utc)

        while True:
            message = 'OK'
            level = 'debug'

            try:
                self._cache.connect()

                self._cache['harvest']['api_nodes'].update_one(filter={"hostname": getfqdn()},
                                                               upsert=True,
                                                               update={"$set": {"hostname": getfqdn(),
                                                                                "ip": gethostbyname(getfqdn()),
                                                                                "os": platform.system(),
                                                                                "plugins": list(PluginRegistry.modules.values()),
                                                                                "version": self._version,
                                                                                "start": start_datetime,
                                                                                "last": datetime.now(tz=timezone.utc)
                                                                                }
                                                                       }
                                                               )

            except Exception as ex:
                message = ' '.join(ex.args)
                level = 'error'

            finally:
                from time import sleep

                getattr(logger, level)(f'{self._cache.log_prefix}: api heartbeat: {message}')
                sleep(5)
