import os
import json
from typing import Dict, Any, Optional

def load_config(override_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Cascading config loading:
    1. Runtime override (if provided)
    2. Project specific: ./.polymath/config.json
    3. User global: ~/.polymath/config.json
    4. Package default: (Installed dir)/.polymath/config.json
    """
    if override_path and os.path.exists(override_path):
        return json.load(open(override_path, "r"))

    # 1. Project Level
    cwd_config = os.path.join(os.getcwd(), ".polymath", "config.json")
    if os.path.exists(cwd_config):
        return json.load(open(cwd_config, "r"))
    
    # 2. User Level
    home_config = os.path.expanduser("~/.polymath/config.json")
    if os.path.exists(home_config):
        return json.load(open(home_config, "r"))

    # 3. Package Default (Fallback)
    # src/core/config.py -> src/core -> src -> polymath root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pkg_config = os.path.join(base_dir, ".polymath", "config.json")
    
    if os.path.exists(pkg_config):
        return json.load(open(pkg_config, "r"))
        
    # Final Fallback
    return {"mcpServers": {}}
