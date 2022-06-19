from typing import Any, Dict, List, Set
from collections import defaultdict


def params_parser(payload: Dict) -> Dict[str, List[Any]]:
    """
    Converts from:
    {
        "name": "\\IGB\\Property\\Custom\\Doelsite\\Vdab\\Sjabloon",
        "params": [
            {"param": "credentials"},
            {"param": "term1"},
            {"param": "term2"},
            {"term1": {"field": "title"}},
            {"term2": {"field": "description"}},
        ],
    }

    to:
    {
        "term1": [{"field": "title"}],
        "term2": [{"field": "description"}],
    }
    """
    ret = defaultdict(list)
    # extract all params names from the payload (eg: term, credentials)
    param_names: Set[str] = {
        child["param"] for child in payload.get("params", []) if "param" in child
    }
    # for each param, check to see if we have a rule with it's name as key
    for param_info in payload.get("params", []):
        # check for {'term': {'field': 'title'}} when param_info=term
        param_name_as_key = set(param_info.keys()).intersection(param_names)
        if not param_name_as_key:
            # the param name doesn't have a custom source, so we can skip it
            continue
        # we will be getting only the first value, since igb returns array for single value
        param_name = param_name_as_key.pop()
        ret[param_name] = param_info[param_name]

    if ret:
        return {
            "params_source": dict(ret),
        }
    return {}
