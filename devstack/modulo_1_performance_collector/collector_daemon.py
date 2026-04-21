from __future__ import annotations

import configparser
import logging
import signal
import sys
import time

print("[DEBUG] collector_daemon module imported", flush=True)

from cinder import context as cinder_context
from cinder.volume.performance_weighted_scheduler_module1.collector_service import (
    PerformanceCollectorService,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

LOG = logging.getLogger(__name__)

CINDER_CONF_PATH = "/etc/cinder/cinder.conf"
_SHOULD_STOP = False


def _handle_signal(signum, frame) -> None:
    global _SHOULD_STOP
    print(f"[DEBUG] received signal {signum}", flush=True)
    LOG.info("Received signal %s, stopping collector daemon", signum)
    _SHOULD_STOP = True


def _load_interval_from_conf(conf_path: str) -> int:
    print(f"[DEBUG] loading interval from conf_path='{conf_path}'", flush=True)

    parser = configparser.ConfigParser(interpolation=None)
    read_files = parser.read(conf_path)

    print(f"[DEBUG] parser.read returned: {read_files}", flush=True)

    if not read_files:
        LOG.warning(
            "Unable to read '%s', using default performance_collector_interval=30",
            conf_path,
        )
        return 30

    value = parser.get("DEFAULT", "performance_collector_interval", fallback="30")

    print(f"[DEBUG] performance_collector_interval raw value='{value}'", flush=True)

    try:
        interval = int(value)

        if interval <= 0:
            raise ValueError("Interval must be positive")

        print(f"[DEBUG] parsed interval={interval}", flush=True)
        return interval

    except Exception as exc:
        print(f"[DEBUG] failed to parse interval: {exc}", flush=True)

        LOG.warning(
            "Invalid performance_collector_interval='%s' in '%s', using default 30",
            value,
            conf_path,
        )
        return 30


def main() -> int:
    global _SHOULD_STOP

    print("[DEBUG] entering main()", flush=True)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    print("[DEBUG] signal handlers registered", flush=True)

    interval = _load_interval_from_conf(CINDER_CONF_PATH)

    print(f"[DEBUG] interval loaded: {interval}", flush=True)

    LOG.info(
        "Starting Performance Collector daemon with interval=%s seconds, conf_path='%s'",
        interval,
        CINDER_CONF_PATH,
    )

    print("[DEBUG] creating PerformanceCollectorService", flush=True)

    collector = PerformanceCollectorService(conf_path=CINDER_CONF_PATH)

    print("[DEBUG] PerformanceCollectorService created", flush=True)

    admin_context = cinder_context.get_admin_context()

    print("[DEBUG] admin_context created", flush=True)

    while not _SHOULD_STOP:
        try:
            print("[DEBUG] starting periodic collection cycle", flush=True)

            LOG.info("Starting periodic collection cycle")

            collector.update_all_backend_metrics(admin_context)

            LOG.info("Completed periodic collection cycle")

            print("[DEBUG] completed periodic collection cycle", flush=True)

        except Exception as exc:
            print(f"[DEBUG] periodic collection failed: {exc}", flush=True)
            LOG.exception("Periodic metrics collection failed")

        if _SHOULD_STOP:
            print("[DEBUG] stop flag detected, breaking loop", flush=True)
            break

        print(f"[DEBUG] sleeping for {interval} seconds", flush=True)
        time.sleep(interval)

    LOG.info("Performance Collector daemon stopped")

    print("[DEBUG] collector daemon stopped", flush=True)

    return 0


if __name__ == "__main__":
    try:
        print("[DEBUG] __main__ entrypoint reached", flush=True)
        sys.exit(main())
    except Exception as exc:
        import traceback

        print(f"[FATAL] collector_daemon crashed: {exc}", flush=True)
        traceback.print_exc()
        raise