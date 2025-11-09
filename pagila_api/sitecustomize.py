import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

try:
    import pydantic.networks as _pydantic_networks
    from pydantic import AnyUrl
    _pydantic_networks.Url = AnyUrl                              
except Exception:
    pass
