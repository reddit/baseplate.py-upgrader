from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


class FixCassExecutionProfiles(BaseplateBaseFix):
    PATTERN = "power< 'CQLMapperContextFactory' any* >"

    def transform(self, node: LN, capture: Capture) -> None:
        self.warn(
            node,
            "Consider using execution profiles to control Cassandra settings. "
            "See: https://git.io/JvSqs",
        )
