#!/bin/bash
set -euo pipefail
umask 077
cd /opt/thesis-research/options-episode-20260911
exec 9>launch-options-20260915.lock
flock -n 9
exec >launch-options-20260915.log 2>&1
date -u '+finite launch entered %Y-%m-%dT%H:%M:%SZ'
research_delay=$((1789462680 - $(date -u +%s)))
if [ "$research_delay" -gt 1200 ]; then exit 41; fi
if [ "$research_delay" -gt 0 ]; then sleep "$research_delay"; fi
if [ "$(date -u +%s)" -ge 1789462740 ]; then exit 42; fi
printf '%s  %s\n' '07b53240e7967d209e98de426f50da05865cc4f4f203357e05e5ba1008cd33a3' '/opt/thesis-research/options-episode-20260911/release-ebc21e9/release_bootstrap.py' | sha256sum -c -
date -u '+verified bootstrap execution %Y-%m-%dT%H:%M:%SZ'
exec /opt/thesis-research/options-episode-20260911/runtime/cpython-3.13.13-linux-x86_64-gnu/bin/python3.13 -I -B /opt/thesis-research/options-episode-20260911/release-ebc21e9/release_bootstrap.py /opt/thesis-research/options-episode-20260911/release-ebc21e9 /opt/thesis-research/options-episode-20260911/data 8349daecd93b39ed2e41e48194b58790706edaf209cf2a3b24ba62b0b430eccf
