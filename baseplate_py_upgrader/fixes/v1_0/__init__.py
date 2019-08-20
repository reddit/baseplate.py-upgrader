import logging
import re

from pathlib import Path
from typing import Match
from typing import Optional

from ...refactor import refactor_python_files
from ...requirements import RequirementsFile
from ...wheelhouse import Wheelhouse


RENAMES = {
    "baseplate._compat": None,
    "baseplate.config": "baseplate.lib.config",
    "baseplate.context": "baseplate.clients",
    "baseplate.core.AuthenticationToken": "baseplate.lib.edge_context.AuthenticationToken",
    "baseplate.core.AuthenticationTokenValidator": "baseplate.lib.edge_context.AuthenticationTokenValidator",
    "baseplate.core": "baseplate",
    "baseplate.core.EdgeRequestContext": "baseplate.lib.edge_context.EdgeRequestContext",
    "baseplate.core.EdgeRequestContextFactory": "baseplate.lib.edge_context.EdgeRequestContextFactory",
    "baseplate.core.InvalidAuthenticationToken": "baseplate.lib.edge_context.InvalidAuthenticationToken",
    "baseplate.core.NoAuthenticationError": "baseplate.lib.edge_context.NoAuthenticationError",
    "baseplate.core.OAuthClient": "baseplate.lib.edge_context.OAuthClient",
    "baseplate.core.Service": "baseplate.lib.edge_context.Service",
    "baseplate.core.Session": "baseplate.lib.edge_context.Session",
    "baseplate.core.User": "baseplate.lib.edge_context.User",
    "baseplate.core.ValidatedAuthenticationToken": "baseplate.lib.edge_context.ValidatedAuthenticationToken",
    "baseplate.crypto": "baseplate.lib.crypto",
    "baseplate.crypto.constant_time_compare": "hmac.compare_digest",
    "baseplate.datetime": "baseplate.lib.datetime",
    "baseplate.diagnostics": "baseplate.observers",
    "baseplate.diagnostics.tracing.publisher": "baseplate.sidecars.trace_publisher",
    "baseplate.error_reporter_from_config": "baseplate.observers.sentry.error_reporter_from_config",
    "baseplate.events": "baseplate.lib.events",
    "baseplate.events.publisher": "baseplate.sidecars.event_publisher",
    "baseplate.events.publisher.gzip_compress": "gzip.compress",
    "baseplate.events.publisher.V1Batch": None,
    "baseplate.events.queue": "baseplate.lib.events",
    "baseplate.events.queue.Event": None,
    "baseplate.events.queue.FieldKind": None,
    "baseplate.events.queue.serialize_v1_event": None,
    "baseplate.experiments": "baseplate.lib.experiments",
    "baseplate.file_watcher": "baseplate.lib.file_watcher",
    "baseplate.frameworks.wrapped_context": None,
    "baseplate.integration": "baseplate.frameworks",
    "baseplate.integration.pyramid.TRACE_HEADER_NAMES": None,
    "baseplate.integration.thrift._extract_trace_info": None,
    "baseplate.integration.thrift.TRACE_HEADER_NAMES": None,
    "baseplate.integration.thrift.RequestContext": "baseplate.RequestContext",
    "baseplate.live_data": "baseplate.lib.live_data",
    "baseplate.live_data.watcher": "baseplate.sidecars.live_data_watcher",
    "baseplate.message_queue": "baseplate.lib.message_queue",
    "baseplate.metrics": "baseplate.lib.metrics",
    "baseplate.metrics_client_from_config": "baseplate.lib.metrics.metrics_client_from_config",
    "baseplate.queue_consumer": "baseplate.frameworks.queue_consumer",
    "baseplate.queue_consumer.ConsumerContext": "baseplate.RequestContext",
    "baseplate.random": "baseplate.lib.random",
    "baseplate.ratelimit": "baseplate.lib.ratelimit",
    "baseplate.requests": "baseplate.lib._requests",
    "baseplate.retry": "baseplate.lib.retry",
    "baseplate.secrets": "baseplate.lib.secrets",
    "baseplate.secrets.fetcher": "baseplate.sidecars.secrets_fetcher",
    "baseplate.secrets.store": "baseplate.lib.secrets",
    "baseplate.service_discovery": "baseplate.lib.service_discovery",
    "baseplate.thrift_pool": "baseplate.lib.thrift_pool",
    "baseplate.tracing_client_from_config": "baseplate.observers.tracing.tracing_client_from_config",
    "baseplate._utils": "baseplate.lib",
    "baseplate._utils.Batch": "baseplate.sidecars.Batch",
    "baseplate._utils.BatchFull": "baseplate.sidecars.BatchFull",
    "baseplate._utils.RawJSONBatch": "baseplate.sidecars.RawJSONBatch",
    "baseplate._utils.SerializedBatch": "baseplate.sidecars.SerializedBatch",
    "baseplate._utils.TimeLimitedBatch": "baseplate.sidecars.TimeLimitedBatch",
}


BASEPLATE_NAME_RE = re.compile(r"(?P<name>baseplate\.(?:[A-Za-z_][A-Za-z0-9_]*\.?)+)")


class NameRemovedError(Exception):
    def __init__(self, name: str):
        super().__init__(
            f"{repr(name)} does not exist anymore. Remove references to it."
        )


def get_new_name(name: str) -> Optional[str]:
    """Find the most appropriate replacement for a name.

    This prefers longest (more-specific) matches over shorter ones. If the
    symbol does not need to be renamed, None is returned.

    """
    for old, new in sorted(RENAMES.items(), key=lambda i: len(i[0]), reverse=True):
        if name == old or name.startswith(old + "."):
            if new is None:
                raise NameRemovedError(old)

            try:
                return name.replace(old, new, 1)
            except KeyError:
                return None
    return None


def replace_module_references(corpus: str) -> str:
    """Replace references to modules in a body of text."""

    def replace_name(m: Match[str]) -> str:
        old_name = m["name"]
        try:
            new_name = get_new_name(old_name)
        except NameRemovedError:
            new_name = None
        return new_name or old_name

    return BASEPLATE_NAME_RE.sub(replace_name, corpus, re.MULTILINE)


def update(
    root: Path, requirements_file: RequirementsFile, wheelhouse: Wheelhouse
) -> int:
    wheelhouse.ensure(requirements_file, "cassandra-driver>=3.13.0")
    wheelhouse.ensure(requirements_file, "cqlmapper>=0.1.0")
    wheelhouse.ensure(requirements_file, "gevent>=1.3")
    wheelhouse.ensure(requirements_file, "hvac>=0.2.17")
    wheelhouse.ensure(requirements_file, "kazoo>=2.5.0")
    wheelhouse.ensure(requirements_file, "kombu>=4.0.0")
    wheelhouse.ensure(requirements_file, "posix_ipc>=1.0.0")
    wheelhouse.ensure(requirements_file, "pyjwt>=1.6.0")
    wheelhouse.ensure(requirements_file, "pymemcache>=1.3.0,<=2.0.0")
    wheelhouse.ensure(requirements_file, "pyramid>=1.9.0")
    wheelhouse.ensure(requirements_file, "redis>=2.10.0,<=3.0.0")
    wheelhouse.ensure(requirements_file, "requests>=2.21.0")
    wheelhouse.ensure(requirements_file, "sqlalchemy>=1.1.0")
    wheelhouse.ensure(requirements_file, "thrift>=0.12.0")

    refactor_python_files(root, __name__)

    for path in root.glob("**/*"):
        if path.suffix in (".ini", ".txt", ".md", ".rst"):
            try:
                old = path.read_text("utf8")
                new = replace_module_references(old)
                if new != old:
                    logging.info("Updated references in %s", path)
                    with path.open("w", encoding="utf8") as f:
                        f.write(new)
            except OSError as exc:
                logging.warning("Can't fix references in %s: %s", path, exc)

    return 0
