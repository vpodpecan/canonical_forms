#!/bin/sh

# patching reldi-tokeniser for multi-threaded environment
echo "Patching tokeniser.py..."
sed -i 's/signal(/pass;#signal(/g' /usr/local/lib/python3.8/site-packages/classla/submodules/reldi_tokeniser/tokeniser.py

# pre-download models
python -c "import classla;classla.download('sl', logging_level='INFO')"

exec "$@"
