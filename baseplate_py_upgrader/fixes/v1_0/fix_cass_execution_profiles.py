# this comment is here to prevent reorder-python-imports from getting confused
# because there are _only_ relative imports. remove as soon as some other
# import comes first.

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
