# Ported from https://github.com/Notenlish/pygame_ecs for comparism

import subprocess
import sys

from statistics import mean, median, stdev


def run(mode):
    res = subprocess.run(f"py speed_test.py {mode}", capture_output=True).stdout.decode('utf-8')
    print(res, end='')
    return float(res.split()[1])

for mode in ['perfect', 'imperfect', 'mixed']:
    times = []
    for _ in range(5):
        times.append(run(mode))

    print(f'{mean(times)=}  {median(times)=}  {stdev(times)=}')
    print()
