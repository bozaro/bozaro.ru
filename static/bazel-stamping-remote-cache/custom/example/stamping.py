#!/usr/bin/env python3
# -*- coding: utf8 -*-
import argparse
import re


def ParseStampFile(filename):
    with open(filename, 'rb') as f:
        return ParseStamp(f.read().decode('utf-8'))


def ParseStamp(data):
    vars = dict()
    for line in data.split("\n"):
        sep = line.find(' ')
        if sep >= 0:
            vars[line[:sep]] = line[sep + 1:]
    return vars


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stamp", action='append', help='The stamp variables file')
    parser.add_argument("--template", help="Input file", type=argparse.FileType('r'))
    parser.add_argument("--output", help="Output file", type=argparse.FileType('w'))
    args = parser.parse_args()

    stamp = dict()
    if args.stamp:
        for stamp_file in args.stamp:
            stamp.update(ParseStampFile(stamp_file))

    template = args.template.read()
    result = re.sub(r'\{(\w+)\}', lambda m: stamp.get(m.group(1), m.group(0)), template)
    args.output.write(result)


if __name__ == '__main__':
    main()
