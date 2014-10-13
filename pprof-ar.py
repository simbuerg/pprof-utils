#!/usr/bin/env python2.7

import argparse
import pprof


def parseArguments():
    description = 'pprof-ar is a simple replacement for ar.'

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-prg', action='store_true',
                        help='Show the compilation progress')
    parser.add_argument('-commands', help='print command lines executed',
                        action='store_true')
    parser.add_argument('flags')
    parser.add_argument('outFile')
    parser.add_argument('-o', dest='output',
                        help='the name of the output file')
    parser.add_argument('files', nargs='*')
    arguments, argv = parser.parse_known_args()

    return arguments


def main():
    args = parseArguments()

    commandLine = ['ar', args.flags, args.outFile] + args.files
    pprof.log_exec(args, commandLine, 'Invoke native AR')


if __name__ == '__main__':
    main()
