#!/bin/bash
set -x

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$PLUGIN_DIR/module1_collector.sh"
source "$PLUGIN_DIR/module2_weigher.sh"

echo ">>> [PLUGIN] fase: $1 / $2"

if [[ "$1" == "stack" && "$2" == "install" ]]; then
    install_sysstat || exit 1
    install_performance_collector || exit 1
    install_weigher_extension || exit 1

elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    configure_performance_collector || exit 1
    configure_weigher_extension || exit 1
    install_storage_bonus_config || exit 1
    start_performance_collector_daemon || exit 1

elif [[ "$1" == "unstack" ]]; then
    stop_performance_collector_daemon || exit 1
    uninstall_performance_collector || exit 1
    uninstall_weigher_extension || exit 1
    uninstall_storage_bonus_config || exit 1
    uninstall_sysstat || exit 1
fi