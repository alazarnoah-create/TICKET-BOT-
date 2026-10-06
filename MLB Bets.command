#!/bin/bash
# Double-click in Finder to see today's MLB bets.
cd "$(dirname "$0")"
bash bets
echo
read -n 1 -s -r -p "Press any key to close"
