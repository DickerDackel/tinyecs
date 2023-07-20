import sys
import os.path
import argparse

from importlib import import_module, invalidate_caches
from importlib.resources import contents


def main():
    cmdline = argparse.ArgumentParser(description='tinyecs demo runner')
    cmdline.add_argument('cmd', type=str, nargs='?', default='ls', help='ls or demo name')
    opts = cmdline.parse_args(sys.argv[1:])

    match opts.cmd:
        case 'ls':
            print('Available demos:')
            demos = [os.path.splitext(f)[0] for f in contents('tinyecs.demos') if not f.startswith('__')]
            for demo in demos:
                print(f'    {demo}')

        case _:
            fullname = f'tinyecs.demos.{opts.cmd}'
            imp = import_module(fullname)
            fkt = getattr(imp, 'main')
            fkt()


if __name__ == '__main__':
    main()
