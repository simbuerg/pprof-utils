#!/usr/bin/env python2.7

import argparse

import pprof


LD = 'ld.gold'
LD_PATH = []


def parseArguments():
    description = 'pprof-ld is a simple replacement for ld.'

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('files', nargs='+')
    parser.add_argument('-commands', help='print command lines pprof.log_executed',
                        action='store_true')
    parser.add_argument('-cpp', help='cpp mode',
                        action='store_true')
    parser.add_argument('-prg', action='store_true',
                        help='show the compilation progress')
    parser.add_argument('-l', action='append', dest='libraries', default=[],
                        help='library flags to pass to the linker')
    parser.add_argument('-L', action='append', dest='librarypath', default=[],
                        help='library paths to pass to the linker')
    parser.add_argument('-x', action='store_true',
                        help='strip all local symbols')
    parser.add_argument('-fPIC', action='store_true',
                        help='Position-Independent Code')
    parser.add_argument('-fpic', action='store_true',
                        help='Position-Independent Code')
    parser.add_argument(
        '-o', dest='output', help='the name of the output file')
    arguments, argv = parser.parse_known_args()

    if argv:
        arguments.unknown_args = filter(lambda x: x[0] == '-', argv)
        arguments.files = arguments.files + filter(lambda x: x[0] != '-', argv)
    else:
        arguments.unknown_args = []

    return arguments


def strip_all(args):
    commandLine = [LD, '-plugin', pprof.PLUGIN, '-plugin-opt', 'emit-llvm', '-o',
                   args.output, '-x'] + args.files + args.unknown_args
    pprof.log_exec(args, commandLine, 'Strip all local symbols')


def main():
    args = parseArguments()

    if args.x:
        strip_all(args)
        exit(0)

    ir = pprof.link_ir(args, [])

    # pprof.link(ir, args, [])
    pprof.link_fortran(ir, args, [])


if __name__ == '__main__':
    main()
