#!/bin/bash

install_sysstat() {
    echo ">>> [PLUGIN] Installazione sysstat"

    if command -v iostat >/dev/null 2>&1; then
        echo ">>> [PLUGIN] iostat già installato"
    else
        sudo apt-get update
        sudo apt-get install -y sysstat || return 1
        echo ">>> [PLUGIN] sysstat installato correttamente"
    fi
}


uninstall_sysstat() {
    echo ">>> [PLUGIN] Disinstallazione sysstat"

    if dpkg -s sysstat >/dev/null 2>&1; then
        sudo apt-get remove -y sysstat || return 1
        sudo apt-get autoremove -y || return 1
        echo ">>> [PLUGIN] sysstat rimosso correttamente"
    else
        echo ">>> [PLUGIN] sysstat non installato, niente da rimuovere"
    fi
}

install_performance_collector() {
    local SRC_DIR="/opt/stack/performance-weighted-scheduler/devstack/modulo_1_performance_collector"
    local DST_DIR="/opt/stack/cinder/cinder/volume/performance_weighted_scheduler_module1"

    echo ">>> [PLUGIN] Installazione Modulo 1 - Performance Collector"
    echo ">>> [PLUGIN] SRC_DIR = $SRC_DIR"
    echo ">>> [PLUGIN] DST_DIR = $DST_DIR"

    [[ -d "$SRC_DIR" ]] || { echo ">>> [PLUGIN][ERRORE] Directory sorgente non trovata: $SRC_DIR"; return 1; }

    mkdir -p "$DST_DIR" || return 1
    touch "$DST_DIR/__init__.py" || return 1

    cp "${SRC_DIR}"/*.py "$DST_DIR"/ || return 1

    echo ">>> [PLUGIN] Modulo 1 copiato correttamente"
}

uninstall_performance_collector() {
    local DST_DIR="/opt/stack/cinder/cinder/volume/performance_weighted_scheduler_module1"

    echo ">>> [PLUGIN] Disinstallazione Modulo 1 - Performance Collector"
    echo ">>> [PLUGIN] DST_DIR = $DST_DIR"

    if [[ -d "$DST_DIR" ]]; then
        rm -rf "$DST_DIR" || return 1
        echo ">>> [PLUGIN] Modulo 1 rimosso correttamente"
    else
        echo ">>> [PLUGIN] Cartella Modulo 1 non presente, niente da rimuovere"
    fi
}

configure_performance_collector() {
    local CONF="/etc/cinder/cinder.conf"
    local CURRENT_INTERVAL

    echo ">>> [PLUGIN] Configurazione Modulo 1 - Performance Collector"

    [[ -f "$CONF" ]] || {
        echo ">>> [PLUGIN][ERRORE] File di configurazione non trovato: $CONF"
        return 1
    }

    iniset "$CONF" DEFAULT debug True || return 1

    CURRENT_INTERVAL=$(iniget "$CONF" DEFAULT performance_collector_interval)

    if [[ -z "$CURRENT_INTERVAL" ]]; then
        iniset "$CONF" DEFAULT performance_collector_interval 30 || return 1
        echo ">>> [PLUGIN] performance_collector_interval non presente, imposto default = 30"
    else
        echo ">>> [PLUGIN] performance_collector_interval già configurato = $CURRENT_INTERVAL"
    fi
}


start_performance_collector_daemon() {
    local CINDER_DIR="/opt/stack/cinder"
    local MODULE1_PKG="cinder.volume.performance_weighted_scheduler_module1.collector_daemon"
    local LOG_FILE="/tmp/performance_weighted_scheduler_collector.log"
    local PID_FILE="/tmp/performance_weighted_scheduler_collector.pid"

    echo ">>> [PLUGIN] Avvio collector periodico"
    echo ">>> [PLUGIN] CINDER_DIR = $CINDER_DIR"
    echo ">>> [PLUGIN] MODULE1_PKG = $MODULE1_PKG"

    if [[ -f "$PID_FILE" ]] && ps -p "$(cat "$PID_FILE")" >/dev/null 2>&1; then
        echo ">>> [PLUGIN] Collector già in esecuzione con PID $(cat "$PID_FILE")"
        return 0
    fi

    cd "$CINDER_DIR" || return 1

    nohup python3 -m "$MODULE1_PKG" >"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"

    echo ">>> [PLUGIN] Collector periodico avviato con PID $(cat "$PID_FILE")"
    echo ">>> [PLUGIN] Log collector: $LOG_FILE"
}

stop_performance_collector_daemon() {
    local PID_FILE="/tmp/performance_weighted_scheduler_collector.pid"

    echo ">>> [PLUGIN] Arresto collector periodico"

    if [[ -f "$PID_FILE" ]]; then
        kill "$(cat "$PID_FILE")" || true
        rm -f "$PID_FILE"
        echo ">>> [PLUGIN] Collector periodico arrestato"
    else
        echo ">>> [PLUGIN] Nessun PID file trovato, niente da arrestare"
    fi
}
