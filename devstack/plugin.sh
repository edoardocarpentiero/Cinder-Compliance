#!/bin/bash

# Nome plugin
PLUGIN_NAME="cinder-compliance"

echo ">>> [$PLUGIN_NAME] plugin.sh caricato"

# DevStack chiama questo file così:
# source plugin.sh stack install
# source plugin.sh stack post-config
# source plugin.sh stack extra
# source plugin.sh unstack clean

if [[ "$1" == "stack" ]]; then

    if [[ "$2" == "install" ]]; then
        echo ">>> [$PLUGIN_NAME] INSTALL phase"
    fi

    if [[ "$2" == "post-config" ]]; then
        echo ">>> [$PLUGIN_NAME] POST-CONFIG phase"
    fi

    if [[ "$2" == "extra" ]]; then
        echo ">>> [$PLUGIN_NAME] EXTRA phase"
    fi

fi

if [[ "$1" == "unstack" ]]; then
    echo ">>> [$PLUGIN_NAME] UNSTACK phase"
fi

if [[ "$1" == "clean" ]]; then
    echo ">>> [$PLUGIN_NAME] CLEAN phase"
fi