import asyncio


class Timer:
    def __init__(self, interval, callback):
        self._enabled = True
        self._interval = interval
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        while self._enabled:
            await self._callback()
            await asyncio.sleep(self._interval.seconds)

    def cancel(self):
        self._enabled = False
        self._task.cancel()
