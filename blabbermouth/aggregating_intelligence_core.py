import random

import attr

from blabbermouth.intellegence_core import IntellegenceCore


@attr.s
class AggregatingIntelligenceCore(IntellegenceCore):
    cores = attr.ib()

    def conceive(self):
        return self._choose_core().conceive()

    def respond(self, user, message):
        return self._choose_core().respond(user, message)

    def _choose_core(self):
        return random.choice(self.cores)
