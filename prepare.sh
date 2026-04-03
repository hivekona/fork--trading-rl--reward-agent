#!/bin/bash
set -e

echo "=== Preparing Trading RL Environment ==="

# Create venv if needed
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install stable-baselines3 gymnasium rich

# Pre-cache ticker data (runs once, cached for subsequent runs)
echo "Pre-caching ticker data for 500 tickers..."
python3 -c "
from rl.data.loader import load_universe
data = load_universe('mega_universe.json', max_tickers=500)
print(f'Cached {len(data)} tickers')
"

echo "=== Preparation Complete ==="
