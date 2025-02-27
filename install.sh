#!/bin/zsh
python3 -m venv myskoxe-env
. myskoxe-env/bin/activate

python3 -m pip install -r requirements.txt
python3 -m pip install -e .

echo -e "\e[32m ✓ Done!\e[0m"