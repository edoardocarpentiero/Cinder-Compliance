from __future__ import annotations

import signal
import sys
import time

from oslo_config import cfg
from oslo_log import log as logging

from cinder import context as cinder_context
from cinder.volume.performance_weighted_scheduler_module1.collector_service import (
    PerformanceCollectorService,
)

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

_SHOULD_STOP = False


def _handle_signal(signum, frame) -> None:
    global _SHOULD_STOP
    LOG.info("Received signal %s, stopping collector daemon", signum)
    _SHOULD_STOP = True


def main() -> int:
    global _SHOULD_STOP

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    interval = int(getattr(CONF, "performance_collector_interval", 30) or 30)

    LOG.info("Starting Performance Collector daemon with interval=%s seconds", interval)

    collector = PerformanceCollectorService()
    admin_context = cinder_context.get_admin_context()

    while not _SHOULD_STOP:
        try:
            collector.update_all_backend_metrics(admin_context)
        except Exception:
            LOG.exception("Periodic metrics collection failed")

        if _SHOULD_STOP:
            break

        time.sleep(interval)

    LOG.info("Performance Collector daemon stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())