# Local AI Reasoning & Creation Engine — task runner.
# Software targets run anywhere; hardware targets are in mac/*.sh (Mac Studio).

PY := python3
SOURCE ?= corpus/coding
OUT ?= data
SYSTEM_PROMPT ?= prompts/coding-system.txt

.PHONY: test test-converter test-router test-ab test-pipeline eval-router \
        inventory convert

test: test-converter test-router test-ab test-pipeline eval-router

test-converter:
	$(PY) -m unittest discover -s converter/tests

test-router:
	$(PY) -m unittest discover -s router/tests

test-ab:
	$(PY) -m unittest discover -s ab/tests

test-pipeline:
	$(PY) -m unittest discover -s orchestrator/tests

eval-router:
	$(PY) router/eval/eval_router.py

inventory:
	$(PY) inventory/inventory.py --source $(SOURCE) --out inventory.md

convert:
	$(PY) converter/convert.py --source $(SOURCE) --out $(OUT) \
		--system-prompt-file $(SYSTEM_PROMPT)
