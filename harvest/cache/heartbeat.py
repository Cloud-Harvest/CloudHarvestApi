from cache.connection import HarvestCacheConnection
from logging import getLogger

logger = getLogger('harvest')


class HarvestCacheHeartBeatThread:
    def __init__(self, writer: HarvestCacheConnection, version: str):
        self._version = version
        self._writer = writer

        from threading import Thread
        self.thread = Thread(target=self._run, name='cache_heartbeat', daemon=True)

        self.thread.start()

    def _run(self):
        import platform
        from socket import getfqdn
        from datetime import datetime, timezone

        start_datetime = datetime.now(tz=timezone.utc)

        while True:
            message = 'OK'

            try:
                self._writer.connect()

                self._writer['harvest']['api_nodes'].update_one(filter={"hostname": getfqdn()},
                                                                upsert=True,
                                                                update={"$set": {"hostname": getfqdn(),
                                                                                 "os": platform.system(),
                                                                                 "version": self._version,
                                                                                 "start": start_datetime,
                                                                                 "last": datetime.now(tz=timezone.utc)
                                                                                 }
                                                                        }
                                                                )

            except Exception as ex:
                message = ' '.join(ex.args)

            finally:
                from time import sleep

                logger.debug(f'{self._writer.log_prefix}: api heartbeat: {message}')
                sleep(5)
