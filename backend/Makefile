.PHONY: format lint imports test

# Формат: код + импорты (ruff format + ruff check --fix, правило I сортирует импорты)
format:
	poetry run ruff format .
	poetry run ruff check --fix .

# Только сортировка/фикс импортов
imports:
	poetry run ruff check --select I --fix .

# Проверка без исправлений (для CI)
lint:
	poetry run ruff format --check .
	poetry run ruff check .

test:
	poetry run pytest