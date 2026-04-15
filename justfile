set shell := ["cmd", "/c"]

[group('dev')]
lint dir=".":
    @echo ▶  ruff check
    ruff check --fix --unsafe-fixes --select I {{ dir }}
    @echo ▶  ruff format
    ruff format {{ dir }}
    @echo ▶  mypy
    mypy {{ dir }} --check-untyped-defs

[group('dev')]
lint-check dir=".":
    ruff check --select I {{ dir }}
    ruff format --check {{ dir }}
    mypy {{ dir }} --check-untyped-defs
    