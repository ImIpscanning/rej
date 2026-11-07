"""Optional REA companion detection; REA's engine is independent of REJ."""
from __future__ import annotations
import shutil


def rea_status() -> dict:
    exe = shutil.which('rea')
    return {'installed': exe is not None, 'executable': exe,
            'integrated_java_engine': False,
            'note': 'REA is optional; REJ does not claim Java JAR decompilation via REA.',
            'documentation': 'https://github.com/morluto/rea'}
