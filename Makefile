.PHONY: run replay

run:
	PYTHONPATH=src python -m krako2.api.main

replay:
	PYTHONPATH=src python scripts/replay_events.py
