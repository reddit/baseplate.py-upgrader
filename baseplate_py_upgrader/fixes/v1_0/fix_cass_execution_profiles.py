from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


class FixCassExecutionProfiles(BaseplateBaseFix):
    PATTERN = "power< 'CQLMapperContextFactory' any* >"

    def transform(self, node: LN, capture: Capture) -> None:
        self.warn(
            node,
            "Consider using execution profiles to control Cassandra settings. "
            "See: https://github.com/reddit/baseplate.py-upgrader/wiki/v1.0#cassandra-execution-profiles",
        )
