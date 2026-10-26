"""Save model results as CSV."""
import csv
from pathlib import Path


def save_results(output_dir, rows):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'results.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return output.resolve()
