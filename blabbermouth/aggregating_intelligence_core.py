import random

import attr

from blabbermouth.intelligence_core import IntelligenceCore


@attr.s
class AggregatingIntelligenceCore(IntelligenceCore):
    cores = attr.ib()

    def conceive(self):
        return self._try_cores(lambda core: core.conceive)

    def respond(self, user, message):
        return self._try_cores(lambda core: core.respond(user, message))

    def _try_cores(self, action):
        for core in random.shuffle(self.cores):
            result = action(core)
            if result is not None:
                return result
        return None
