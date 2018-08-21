import random

import attr

from blabbermouth.intelligence_core import IntelligenceCore


@attr.s
class AggregatingIntelligenceCore(IntelligenceCore):
    cores = attr.ib()

    async def conceive(self):
        return await self._try_cores(lambda core: core.conceive())

    async def respond(self, user, message):
        return await self._try_cores(lambda core: core.respond(user, message))

    async def _try_cores(self, coro):
        for core in random.shuffle(self.cores):
            result = await coro(core)
            if result is not None:
                return result
        return None
