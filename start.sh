set -e

PY_BIN="$(command -v python3 || command -v python)"

"$PY_BIN" main.py

read -n 1 -s -r -p "Нажмите любую клавишу для выхода..."
echo