#!/usr/bin/env bash
set -u

for iface in $(ls /sys/class/net); do
    echo "[*] Removing clsact from $iface"

    if sudo tc qdisc del dev "$iface" clsact 2>/tmp/tc_clsact_err; then
        echo "    removed"
    else
        err="$(cat /tmp/tc_clsact_err)"
        if echo "$err" | grep -qiE "No such file|Cannot find|Invalid argument"; then
            echo "    no clsact"
        else
            echo "    failed: $err"
        fi
    fi
done

rm -f /tmp/tc_clsact_err