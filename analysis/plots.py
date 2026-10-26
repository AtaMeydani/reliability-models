"""Save charts from the results calculated during a run."""
from collections import defaultdict
from urllib.parse import quote

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def save_plots(output, rows, mission_time):
    directory = output / 'plots'
    directory.mkdir(parents=True, exist_ok=True)
    groups = defaultdict(list)
    for row in rows:
        groups[(row['scenario'], row['metric'])].append(row)
    paths = []
    for (scenario, metric), values in groups.items():
        times = [row['time'] for row in values]
        figure, axis = plt.subplots(figsize=(9, 4.8))
        axis.plot(times, [row['markov'] for row in values],
                  label='Markov', color='#1768ac', linewidth=2.2)
        axis.plot(times, [row['monte_carlo'] for row in values],
                  label='Monte Carlo', color='#d46a18', linestyle='--', linewidth=1.8)
        axis.axvline(mission_time, color='#555555', linestyle=':', linewidth=1,
                     label=f'Mission time: {mission_time:g} h')
        label = {'reliability': 'Reliability R(t)', 'availability': 'Availability A(t)',
                 'performability': 'Expected service reward (capacity units)'}[metric]
        title = scenario.replace('_', ' ').replace('ccf', 'CCF')
        axis.set(title=f'{title} - {metric.capitalize()}',
                 xlabel='Time (hours)', ylabel=label, xlim=(min(times), max(times)))
        axis.set_ylim(bottom=0)
        if metric != 'performability':
            axis.set_ylim(top=1.03)
        axis.grid(alpha=0.22)
        axis.spines[['top', 'right']].set_visible(False)
        axis.legend(frameon=False)
        figure.tight_layout()
        path = directory / f'{quote(scenario, safe="")}_{metric}.png'
        figure.savefig(path, dpi=180, facecolor='white')
        plt.close(figure)
        paths.append(path)
    return paths
