from __future__ import annotations

import oslo_messaging
from oslo_config import cfg

from cinder.scheduler.performance_weighted_scheduler_module2.metrics_cache import (
    BackendMetricsCache,
)
from cinder.scheduler.performance_weighted_scheduler_module2.scheduler_metrics_endpoint import (
    SchedulerMetricsEndpoint,
)
from cinder.scheduler.performance_weighted_scheduler_module2.volume_rpc_client import (
    VolumeMetricsAPI,
)
from cinder.scheduler.weights.performance_weigher import PerformanceWeigher

CONF = cfg.CONF


def init_scheduler_plugin():
    cache = BackendMetricsCache(ttl_seconds=60)
    volume_rpc_api = VolumeMetricsAPI()

    endpoint = SchedulerMetricsEndpoint(cache=cache)

    transport = oslo_messaging.get_rpc_transport(CONF)
    target = oslo_messaging.Target(
        topic="scheduler_metrics",
        server="scheduler_metrics_server",
    )

    server = oslo_messaging.get_rpc_server(
        transport,
        target,
        [endpoint],
        executor="threading",
    )
    server.start()

    weigher = PerformanceWeigher(
        cache=cache,
        rpc_api=volume_rpc_api,
    )

    return {
        "cache": cache,
        "rpc_server": server,
        "weigher": weigher,
    }