import asyncio
import datetime

import attr


@attr.s(slots=True)
class Timer:
    _callback = attr.ib()
    _task = attr.ib(default=None)
    _enabled = attr.ib(default=True)

    interval = attr.ib(attr.validators.instance_of(datetime.timedelta))

    def __attrs_post_init__(self):
        self._task = asyncio.ensure_future(self._work())
        self._enabled = True

    def enable(self):
        self.disable()

        self._task = asyncio.ensure_future(self._work())
        self._enabled = True

    def disable(self):
        self._task.cancel()
        self._enabled = False

    async def _work(self):
        while self._enabled:
            await asyncio.sleep(self.interval.seconds)
            await self._callback()
