# PLREPORT for FreshBooks

Using the FreshBooks API, export all income and expense receipts.

## Quickstart

```
python3 -m venv env/
source env/bin/activate
pip install -r requirements.txt
cp .env.template .env
# Add your API token and domain
$EDITOR .env
./run.py --year YEAR
```

## Requirements

- Python 3.5
