run : install
	uv run -m src

install: 
	uv sync

clean:
	rm -rf .venv
	rm -rf uv.lock
	rm -rf src/__pycache__