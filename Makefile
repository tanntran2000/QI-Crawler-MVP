.PHONY: install test lint init discover export report serve clean

install:
	python -m pip install -e ".[dev]"
	python -m playwright install chromium

test:
	python -m pytest -q

lint:
	python -m ruff check src tests

init:
	QI-Crawler init-db

discover:
	QI-Crawler discover "https://muasamcong.mpi.gov.vn/web/guest/contractor-selection?render=search" --seconds 90 --headed

export:
	QI-Crawler export --format xlsx --output data/notices.xlsx

report:
	QI-Crawler report-daily

serve:
	QI-Crawler serve

clean:
	python -c "import pathlib,shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache','.ruff_cache','src/qi_crawler.egg-info']]"
