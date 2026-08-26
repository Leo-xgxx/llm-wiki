#!/usr/bin/env bash
# Idempotent dependency setup for the llm-wiki reference validator and tests.
#
# requirements.txt pins PyYAML==6.0, which ships no wheel for Python 3.12 and
# fails to build under Cython 3 (the "'build_ext' object has no attribute
# 'cython_sources'" error). Pin the build toolchain to Cython<3 and disable
# build isolation so the exact pin still installs from source.
set -euo pipefail

PIP=(python3 -m pip install --break-system-packages)

"${PIP[@]}" "Cython<3.0" wheel setuptools
"${PIP[@]}" --no-build-isolation -r requirements.txt

python3 - <<'PY'
import jsonschema
import yaml

print(f"deps ok: PyYAML {yaml.__version__} | jsonschema {jsonschema.__version__}")
PY
