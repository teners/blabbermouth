import asyncio
import datetime

import attr


@attr.s
class Timer:
    callback = attr.ib()
    interval = attr.ib(attr.validators.instance_of(datetime.timedelta))
    task = attr.ib(default=None)
    enabled = attr.ib(default=True)

    def __attrs_post_init__(self):
        self.task = asyncio.ensure_future(self._work())
        self.enabled = True

    def enable(self):
        self.disable()

        self.task = asyncio.ensure_future(self._work())
        self.enabled = True

    def disable(self):
        self.task.cancel()
        self.enabled = False

    async def _work(self):
        while self.enabled:
            await asyncio.sleep(self.interval.seconds)
            await self.callback()
