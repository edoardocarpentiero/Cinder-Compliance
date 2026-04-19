from __future__ import annotations

from typing import Any, Dict

import oslo_messaging
from oslo_config import cfg

CONF = cfg.CONF


class VolumeMetricsAPI:
    RPC_API_VERSION = "1.0"

    def __init__(self) -> None:
        target = oslo_messaging.Target(
            topic="volume_metrics",
            version=self.RPC_API_VERSION,
        )
        transport = oslo_messaging.get_rpc_transport(CONF)
        self.client = oslo_messaging.get_rpc_client(transport, target)

    def fetch_backend_metrics(
        self,
        context: Any,
        backend_name: str,
        storage_type: str,
        device_name: str,
    ) -> Dict[str, Any]:
        cctxt = self.client.prepare()
        return cctxt.call(
            context,
            "fetch_backend_metrics",
            backend_name=backend_name,
            storage_type=storage_type,
            device_name=device_name,
        )