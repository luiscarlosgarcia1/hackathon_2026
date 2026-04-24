.PHONY: install run test clean seed

install:
	pip install -r requirements.txt

run:
	FLASK_APP=run.py flask run --port 5001

test:
	pytest tests/ -v

seed:
	FLASK_APP=run.py flask seed-admin

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f hearings.db instance/hearings.db
