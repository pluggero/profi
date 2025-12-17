"""Context preparation for template rendering."""

import os
import subprocess
from typing import Any, Dict


def compute_dynamic_values(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Pre-compute dynamic values for template rendering.

    Resolves system-dependent values (IP addresses, paths, etc.) before rendering.
    Values are sourced from environment variables (OP_* prefix) and runtime computation.

    Args:
        config: Configuration dictionary from load_config()

    Returns:
        Dictionary of computed values (e.g., {'attacker_ip': '10.10.14.5', ...})
    """
    context = {}

    # Import all OP_* environment variables
    # OP_ATTACKER_IP -> attacker_ip, OP_SHELL_PORT -> shell_port
    for key, value in os.environ.items():
        if key.startswith('OP_'):
            context_key = key[3:].lower()
            context[context_key] = value

    # Compute attacker_ip from network interface if not set
    if 'attacker_ip' not in context or not context['attacker_ip']:
        attacker_interface = context.get('attacker_interface', 'tun0')
        try:
            result = subprocess.run(
                f"ip -f inet addr show {attacker_interface} | awk '/inet / {{print $2}}' | cut -d/ -f1",
                shell=True,
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                context['attacker_ip'] = result.stdout.strip()
            else:
                context['attacker_ip'] = ''
        except (subprocess.TimeoutExpired, Exception):
            context['attacker_ip'] = ''

    return context
