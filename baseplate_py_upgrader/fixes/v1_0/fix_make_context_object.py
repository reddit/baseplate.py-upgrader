from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


class FixMakeContextObject(BaseplateBaseFix):
    PATTERN = "trailer< '.' 'make_server_span' >"

    def transform(self, node: LN, capture: Capture) -> None:
        self.warn(
            node,
            "Ensure the custom context object you pass to make_server_span derives from "
            "RequestContext. See: https://git.io/fj5Xn",
        )
