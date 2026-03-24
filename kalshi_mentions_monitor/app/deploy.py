from __future__ import annotations

import os
import subprocess
from pathlib import Path


def maybe_deploy_dashboard(project_dir: Path) -> dict:
    if os.getenv('KALSHI_DASHBOARD_AUTO_DEPLOY', '').lower() not in {'1', 'true', 'yes'}:
        return {'enabled': False, 'attempted': False}

    script_path = project_dir / 'deploy_dashboard.sh'
    if not script_path.exists():
        return {'enabled': True, 'attempted': False, 'error': f'missing script: {script_path}'}

    try:
        result = subprocess.run(
            [str(script_path)],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            check=False,
            env=os.environ.copy(),
        )
        return {
            'enabled': True,
            'attempted': True,
            'ok': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': (result.stdout or '').strip()[:2000],
            'stderr': (result.stderr or '').strip()[:2000],
        }
    except Exception as exc:  # noqa: BLE001
        return {'enabled': True, 'attempted': True, 'ok': False, 'error': str(exc)}
