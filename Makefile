.PHONY: setup generate ingest preflight benchmark dashboard report demo clean help

setup:
	pip install -r requirements.txt
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env -- fill in your API keys"; fi

# Step 1: generate 6000 synthetic SC judgment cases (30 seconds, no internet needed)
generate:
	python generate_data.py

# Step 2: embed into ChromaDB (required for all pipelines)
ingest:
	python data/ingest.py

# Step 2b: also load into TigerGraph (optional -- needs TG_HOST in .env)
ingest-tg:
	python data/ingest.py both

# Step 3: verify everything is ready before benchmarking
preflight:
	python preflight.py

# Step 4: run the full benchmark (10 queries x 3 pipelines + evaluation)
benchmark:
	python eval/benchmark_1.py

# Step 5: launch the comparison dashboard
dashboard:
	streamlit run dashboard/app.py

report:
	python eval/generate_report.py

# Generate mock results for offline demo (no API keys needed)
demo:
	python eval/mock_results.py
	python eval/generate_report.py
	@echo "Open docs/interactive_demo.html in your browser"

clean:
	rm -rf data/chroma_db data/raw eval/results.csv .cache

help:
	@echo ""
	@echo "LexGraph -- GraphRAG Inference Hackathon by TigerGraph"
	@echo ""
	@echo "Quick start (5 steps):"
	@echo "  make setup       install dependencies + create .env"
	@echo "  make generate    generate 6000 SC judgment cases (~30s)"
	@echo "  make ingest      embed into ChromaDB (~10-20 min)"
	@echo "  make preflight   verify everything is ready"
	@echo "  make benchmark   run 10-query evaluation + scoring"
	@echo ""
	@echo "Optional:"
	@echo "  make ingest-tg   also load into TigerGraph (full multi-hop path)"
	@echo "  make dashboard   start Streamlit comparison dashboard"
	@echo "  make report      generate benchmark_report.md"
	@echo "  make demo        mock results for offline demo"
	@echo "  make clean       remove ChromaDB and cache"
	@echo ""
