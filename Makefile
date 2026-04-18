.PHONY: install run test seed clean

install:
	pip install -r requirements.txt

run:
	ollama serve & OLLAMA_PID=$$!; trap "kill $$OLLAMA_PID" EXIT; sleep 2 && FLASK_APP=run.py flask run

test:
	pytest tests/ -v

seed:
	python scripts/seed.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f instance/hearings.db
