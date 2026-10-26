"""Read scenario data, solve the models, and save the results."""
import argparse
from pathlib import Path

from analysis.artifacts import save_results
from analysis.inputs import read_input
from analysis.plots import save_plots
from analysis.runner import solve_scenario


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path,
                        default=Path(__file__).resolve().parent / 'data' / 'scenarios.json')
    parser.add_argument('--simulations', type=int, help='Override the input repetition count.')
    parser.add_argument('--seed', type=int, help='Set a seed for repeatable simulations.')
    parser.add_argument('--output-dir', default='output')
    args = parser.parse_args()
    if args.seed is not None and args.seed < 0:
        parser.error('seed must be a nonnegative integer.')
    try:
        document = read_input(args.input, args.simulations)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        parser.error(f'Invalid input: {error}')
    settings = document['settings']
    rows = []
    for index, scenario in enumerate(document['scenarios']):
        seed = None if args.seed is None else args.seed + index
        rows.extend(solve_scenario(scenario, settings, seed))
        print(f'Solved: {scenario["name"]}', flush=True)
    output = save_results(args.output_dir, rows)
    plots = save_plots(output, rows, settings['mission_time'])
    print(f'Saved {len(rows)} result rows to {output}', flush=True)
    print(f'Saved {len(plots)} charts to {output / "plots"}', flush=True)


if __name__ == '__main__':
    main()
