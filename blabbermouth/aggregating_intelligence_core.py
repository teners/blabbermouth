import random

import attr

from blabbermouth.intelligence_core import IntelligenceCore


@attr.s
class AggregatingIntelligenceCore(IntelligenceCore):
    cores = attr.ib()

    def conceive(self):
        return self._choose_core().conceive()

    def respond(self, user, message):
        return self._choose_core().respond(user, message)

    def _choose_core(self):
        return random.choice(self.cores)
