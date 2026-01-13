SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export PYTHONPATH="$SCRIPT_DIR/breg:$PYTHONPATH"

ipython --pdb "$SCRIPT_DIR/breg/main.py" -- "$@"