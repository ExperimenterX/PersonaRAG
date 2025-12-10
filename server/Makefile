.PHONY: setup index serve

setup:
\tpip install -r requirements.txt

index:
\tpython -m app.indexing.build_index

serve:
\tuvicorn app.main:app --reload --host 0.0.0.0 --port 8000
