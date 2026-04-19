from __future__ import annotations

import subprocess
from typing import Any, Dict, List, Optional

from oslo_config import cfg
from oslo_log import log as logging

from cinder import context as cinder_context
from cinder.volume.performance_weighted_scheduler_module1.performance_metrics import (
    PerformanceMetricsCollector,
)
from cinder.volume.performance_weighted_scheduler_module1.scheduler_rpc_api import (
    SchedulerMetricsAPI,
)

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PerformanceCollectorService:
    def __init__(self) -> None:
        LOG.info("Initializing PerformanceCollectorService")
        self.collector = PerformanceMetricsCollector()
        self.rpc_api = SchedulerMetricsAPI()

    def _resolve_iostat_device_from_vg(self, volume_group: str) -> Optional[str]:
        try:
            LOG.info("Resolving iostat device from volume group '%s'", volume_group)

            cmd = [
                "pvs",
                "--noheadings",
                "-o",
                "pv_name",
                "--select",
                f"vg_name={volume_group}",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            pv_name = result.stdout.strip()
            if not pv_name:
                LOG.warning("No physical volume found for volume group '%s'", volume_group)
                return None

            device_name = pv_name.split("/")[-1]
            LOG.info(
                "Resolved volume group '%s' to iostat device '%s'",
                volume_group,
                device_name,
            )
            return device_name

        except Exception:
            LOG.exception(
                "Failed to resolve iostat device from volume group '%s'",
                volume_group,
            )
            return None

    def _load_backends_from_conf(self) -> List[Dict[str, Any]]:
        LOG.info("Loading backend configuration from cinder.conf")

        backends: List[Dict[str, Any]] = []

        enabled_backends = getattr(CONF, "enabled_backends", None)
        if not enabled_backends:
            LOG.warning("No enabled_backends configured in cinder.conf")
            return backends

        if isinstance(enabled_backends, str):
            enabled_backends = [b.strip() for b in enabled_backends.split(",") if b.strip()]

        LOG.info("Detected enabled backends: %s", enabled_backends)

        for backend_section in enabled_backends:
            LOG.info("Processing backend section: %s", backend_section)

            group = getattr(CONF, backend_section, None)
            if group is None:
                LOG.warning("Backend section '%s' not found in CONF", backend_section)
                continue

            backend_name = getattr(group, "volume_backend_name", backend_section)
            storage_type = getattr(group, "my_storage_type", "LVM")
            device_name = getattr(group, "iostat_device", None)

            if device_name:
                LOG.info(
                    "Backend '%s': using configured iostat_device '%s'",
                    backend_name,
                    device_name,
                )
            else:
                volume_group = getattr(group, "volume_group", None)
                if volume_group:
                    device_name = self._resolve_iostat_device_from_vg(volume_group)

                if not device_name:
                    LOG.warning(
                        "Backend '%s': unable to determine iostat device automatically; skipping",
                        backend_name,
                    )
                    continue

            backend_info = {
                "backend": backend_name,
                "storage_type": storage_type,
                "device_name": device_name,
                "backend_section": backend_section,
            }

            LOG.info("Backend configuration loaded: %s", backend_info)
            backends.append(backend_info)

        LOG.info("Loaded %d backend configurations", len(backends))
        return backends

    def publish_all_backend_metrics(self, context: Any, backends: List[Dict[str, Any]]) -> None:
        LOG.info("Publishing metrics for %d backends", len(backends))

        for backend in backends:
            backend_name = backend["backend"]
            LOG.info("Collecting metrics for backend '%s'", backend_name)

            try:
                metrics = self.collector.collect_iostat_metrics(
                    backend_name=backend["backend"],
                    storage_type=backend["storage_type"],
                    device_name=backend["device_name"],
                )

                metrics["backend_section"] = backend.get("backend_section")

                self.rpc_api.push_backend_metrics(context, metrics)
                LOG.info("Metrics published successfully for backend '%s'", backend_name)

            except Exception:
                LOG.exception("Failed to collect/publish metrics for backend '%s'", backend_name)

    def update_all_backend_metrics(self, context: Any | None = None) -> None:
        LOG.info("Starting update_all_backend_metrics")

        if context is None:
            context = cinder_context.get_admin_context()

        backends = self._load_backends_from_conf()
        self.publish_all_backend_metrics(context, backends)

        LOG.info("Completed update_all_backend_metrics")