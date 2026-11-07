"""JAR comparison output formatting."""
from pathlib import Path


def format_comparison(report:dict)->str:
    lines=['JAR VERSION COMPARISON','='*48,f"Old: {Path(report['old']).name}",
           f"New: {Path(report['new']).name}",'']
    for key in ('added','removed','modified'):
        values=report[key]
        lines.extend([f'{key.upper()} ({len(values)})','-'*48])
        lines.extend('  '+x for x in values[:300])
        if len(values)>300:
            lines.append(f'  ... {len(values)-300} more')
        lines.append('')
    lines.append(f"Unchanged classes: {report['unchanged_count']}")
    return '\n'.join(lines)
