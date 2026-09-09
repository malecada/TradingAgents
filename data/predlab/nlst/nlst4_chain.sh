#!/bin/bash
cd /home/malecada/master_thesis/TradingAgents-predlab
while ! grep -q "^C done" data/predlab/nlst/nlst4_screen.log; do sleep 60; done
echo "CHAIN: C done seen $(date -u +%FT%TZ)" >> data/predlab/nlst/nlst4_features.log
.venv/bin/python scripts/predlab_nlst4_features.py >> data/predlab/nlst/nlst4_features.log 2>&1
echo "FEATURES_DONE rc=$?" >> data/predlab/nlst/nlst4_features.log
