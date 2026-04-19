from __future__ import annotations

from typing import Any, Dict

from cinder.scheduler import weights
from cinder.scheduler.performance_weighted_scheduler_module2.metrics_cache import (
    BackendMetricsCache,
)
from cinder.scheduler.performance_weighted_scheduler_module2.volume_rpc_client import (
    VolumeMetricsAPI,
)


class PerformanceWeigher(weights.BaseHostWeigher):
    def __init__(
        self,
        cache: BackendMetricsCache,
        rpc_api: VolumeMetricsAPI,
    ) -> None:
        super().__init__()
        self.cache = cache
        self.rpc_api = rpc_api

    def weight_multiplier(self) -> float:
        return 1.0

    def _weigh_object(self, host_state: Any, weight_properties: Dict[str, Any]) -> float:
        backend_name = self._extract_backend_name(host_state)
        storage_type = self._extract_storage_type(host_state)
        device_name = self._extract_device_name(host_state)

        metrics = self.cache.get(backend_name)

        if metrics is None or self.cache.is_stale(backend_name):
            context = weight_properties.get("context")
            metrics = self.rpc_api.fetch_backend_metrics(
                context=context,
                backend_name=backend_name,
                storage_type=storage_type,
                device_name=device_name,
            )
            self.cache.put(backend_name, metrics)

        free_capacity = float(getattr(host_state, "free_capacity_gb", 0) or 0)
        allocated_capacity = float(getattr(host_state, "allocated_capacity_gb", 0) or 0)

        iops = float(metrics.get("iops", 0))
        latency_ms = float(metrics.get("latency_ms", 9999))
        throughput_kb_s = float(metrics.get("throughput_kb_s", 0))
        saturation_pct = float(metrics.get("saturation_pct", 100))

        score = (
            (free_capacity * 0.4)
            + (iops * 0.01)
            + (throughput_kb_s * 0.001)
            - (latency_ms * 0.5)
            - (saturation_pct * 0.1)
            - (allocated_capacity * 0.1)
        )

        return score

    @staticmethod
    def _extract_backend_name(host_state: Any) -> str:
        host = getattr(host_state, "host", "")
        if "@" in host:
            return host.split("@", 1)[1].split("#", 1)[0]
        return host

    @staticmethod
    def _extract_storage_type(host_state: Any) -> str:
        capabilities = getattr(host_state, "capabilities", {}) or {}
        return str(capabilities.get("my_storage_type", "LVM"))

    @staticmethod
    def _extract_device_name(host_state: Any) -> str:
        capabilities = getattr(host_state, "capabilities", {}) or {}
        return str(capabilities.get("iostat_device", ""))