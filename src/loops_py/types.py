from __future__ import annotations

from typing import Any, Dict, List, Union

JSONScalar = Union[str, int, float, bool, None]
JSONType = Union[JSONScalar, Dict[str, Any], List[Any]]
