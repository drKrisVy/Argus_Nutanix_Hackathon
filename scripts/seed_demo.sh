#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

python3 -c "
import sys
sys.path.insert(0, '.')
from codebase_memory.graph_builder import build_graph, save_graph
g = build_graph('data/sample_repo')
save_graph(g, 'graph.json')
print(f'Graph built: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges -> graph.json')
"

echo "Run the tests now:            pytest tests/ -q"
echo "Then launch the dashboard:    streamlit run dashboard/app.py"
