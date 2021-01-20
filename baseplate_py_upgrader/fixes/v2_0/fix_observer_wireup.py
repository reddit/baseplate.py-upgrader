from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


REMOVED_FUNCTIONS = (
    "configure_logging",
    "configure_tagged_metrics",
    "configure_metrics",
    "configure_tracing",
    "configure_error_reporting",
)


class FixObserverWireup(BaseplateBaseFix):
    PATTERN = f"""
        (
           power<
            NAME
            trailer< '.' ({' | '.join("name='{}'".format(name) for name in REMOVED_FUNCTIONS)}) >
            trailer< '(' args=any* ')' >
            any*
          >
        )
    """

    def transform(self, node: LN, capture: Capture) -> None:
        if capture["name"].value in REMOVED_FUNCTIONS:
            self.warn(node, "Use configure_observers(). See: https://git.io/Jt8S7")
