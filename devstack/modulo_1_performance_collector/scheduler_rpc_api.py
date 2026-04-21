from __future__ import annotations

from typing import Any, Dict

import oslo_messaging
from oslo_config import cfg

CONF = cfg.CONF

_CONF_INITIALIZED = False


def _init_conf() -> None:
    global _CONF_INITIALIZED

    print("[DEBUG][scheduler_rpc_api] entering _init_conf()", flush=True)

    if _CONF_INITIALIZED:
        print("[DEBUG][scheduler_rpc_api] CONF already initialized", flush=True)
        return

    CONF(
        args=[],
        project="cinder",
        default_config_files=["/etc/cinder/cinder.conf"],
    )

    _CONF_INITIALIZED = True

    print(
        "[DEBUG][scheduler_rpc_api] RPC configuration loaded from "
        "/etc/cinder/cinder.conf",
        flush=True,
    )


class SchedulerMetricsAPI:
    RPC_API_VERSION = "1.0"

    def __init__(self) -> None:
        print("[DEBUG][scheduler_rpc_api] Initializing SchedulerMetricsAPI", flush=True)

        _init_conf()

        target = oslo_messaging.Target(
            topic="scheduler_metrics",
            version=self.RPC_API_VERSION,
        )

        print(
            f"[DEBUG][scheduler_rpc_api] Target created: topic='{target.topic}', "
            f"version='{target.version}'",
            flush=True,
        )

        print("[DEBUG][scheduler_rpc_api] Creating RPC transport", flush=True)
        transport = oslo_messaging.get_rpc_transport(CONF)

        print("[DEBUG][scheduler_rpc_api] Creating RPC client", flush=True)
        self.client = oslo_messaging.get_rpc_client(transport, target)

        print(
            "[DEBUG][scheduler_rpc_api] SchedulerMetricsAPI initialized successfully",
            flush=True,
        )

    def push_backend_metrics(self, context: Any, metrics: Dict[str, Any]) -> None:
        print(
            f"[DEBUG][scheduler_rpc_api] Sending backend metrics for "
            f"backend='{metrics.get('backend')}'",
            flush=True,
        )

        print(
            f"[DEBUG][scheduler_rpc_api] Payload={metrics}",
            flush=True,
        )

        try:
            cctxt = self.client.prepare()
            print("[DEBUG][scheduler_rpc_api] RPC context prepared", flush=True)

            cctxt.cast(context, "update_backend_metrics", metrics=metrics)

            print(
                f"[DEBUG][scheduler_rpc_api] Metrics sent successfully for "
                f"backend='{metrics.get('backend')}'",
                flush=True,
            )

        except Exception as exc:
            print(
                f"[ERROR][scheduler_rpc_api] Failed to send metrics for "
                f"backend='{metrics.get('backend')}': {exc}",
                flush=True,
            )
            raise