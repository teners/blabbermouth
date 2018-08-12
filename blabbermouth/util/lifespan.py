import datetime
import time

import attr


@attr.s(slots=True)
class Lifespan:
    timeout = attr.ib(validator=attr.validators.instance_of(datetime.timedelta))
    stamp = attr.ib(factory=time.time)

    def __bool__(self):
        return datetime.timedelta(seconds=(time.time() - self.stamp)) < self.timeout

    def reset(self):
        self.stamp = time.time()
