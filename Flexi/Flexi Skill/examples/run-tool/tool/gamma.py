"""Stand-in for your own command-line tool: applies a gamma to a 16-bit PPM.

    python3 gamma.py --gamma 2.2 in.ppm out.ppm
"""
import argparse
import sys

import numpy as np


def read_ppm16(path):
    with open(path, 'rb') as f:
        tokens = []
        while len(tokens) < 4:
            line = f.readline()
            if not line:
                sys.exit(f'{path}: not a PPM file')
            tokens += line.split(b'#')[0].split()
        if tokens[0] != b'P6':
            sys.exit(f'{path}: not a colour PPM file')
        w, h, maxval = int(tokens[1]), int(tokens[2]), int(tokens[3])
        data = np.frombuffer(f.read(), dtype='>u2' if maxval > 255 else np.uint8, count=w * h * 3)
    return data.reshape(h, w, 3).astype(np.float64) / maxval


def write_ppm16(path, image):
    h, w, _ = image.shape
    with open(path, 'wb') as f:
        f.write(b'P6\n%d %d\n65535\n' % (w, h))
        f.write(np.round(np.clip(image, 0, 1) * 65535).astype('>u2').tobytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gamma', type=float, default=2.2)
    parser.add_argument('input')
    parser.add_argument('output')
    args = parser.parse_args()
    if args.gamma <= 0:
        sys.exit(f'gamma must be positive, not {args.gamma}')
    write_ppm16(args.output, read_ppm16(args.input) ** (1 / args.gamma))


if __name__ == '__main__':
    main()
