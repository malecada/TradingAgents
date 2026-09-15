#!/bin/bash
set -euo pipefail
umask 077
cd /opt/thesis-research/options-timing-20260915
exec 9>launch-options-timing-20260915.lock
flock -n 9
set -C
exec >launch-options-timing-20260915.log 2>&1
date -u '+finite launch entered %Y-%m-%dT%H:%M:%SZ'
research_delay=$((1789469880 - $(date -u +%s)))
if [ "$research_delay" -gt 7200 ]; then exit 41; fi
if [ "$research_delay" -gt 0 ]; then sleep "$research_delay"; fi
research_launch_now=$(date -u +%s)
if [ "$research_launch_now" -lt 1789469880 ] || [ "$research_launch_now" -ge 1789469940 ]; then exit 42; fi
printf '%s  %s\n' 'fb123634d66dcf22cb8db49663febb3baf207af64ad3847cdcaa6b9f05ab7b1e' '/opt/thesis-research/options-timing-20260915/release-22bdf6c/release_bootstrap.py' | sha256sum -c -
date -u '+verified bootstrap execution pending final wall-clock check %Y-%m-%dT%H:%M:%SZ'
research_launch_now=$(date -u +%s)
if [ "$research_launch_now" -lt 1789469880 ] || [ "$research_launch_now" -ge 1789469940 ]; then exit 43; fi
exec /opt/thesis-research/options-episode-20260911/runtime/cpython-3.13.13-linux-x86_64-gnu/bin/python3.13 -I -B /opt/thesis-research/options-timing-20260915/release-22bdf6c/release_bootstrap.py /opt/thesis-research/options-timing-20260915/release-22bdf6c /opt/thesis-research/options-timing-20260915/data 375d70df4656f8ad851b038ffaabb0cf61bb71115aadd750ac2d8dc9a933d4a3
