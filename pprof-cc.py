#!/usr/bin/env python2.7
import argparse
import os
import sys

import pprof


def parseArguments():
    """


    :return:
    """
    description = 'polly-profcc is a simple replacement for compiler drivers like ' \
                  'gcc, clang or icc.'

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('files', nargs='*')
    parser.add_argument('-o', dest='output',
                        help='the name of the output file',
                        required=False)
    parser.add_argument('-include', action='append',
                        dest='extra_includes',
                        default=[],
                        help='implicit #include directives')
    parser.add_argument('-I', action='append',
                        dest='incdirs',
                        default=[],
                        help='include search path')
    parser.add_argument('-l', action='append',
                        dest='libraries',
                        default=[],
                        help='library flags to pass to the linker')
    parser.add_argument('-L', action='append',
                        dest='librarypath',
                        default=[],
                        help='library paths to pass to the linker')
    parser.add_argument('-S', action='store_true',
                        default='gnu89',
                        required=False)
    parser.add_argument('-fPIC', action='store_true',
                        help='Position-Independent Code')
    parser.add_argument('-fpic', action='store_true',
                        help='Position-Independent Code')
    parser.add_argument('-prg', action='store_true',
                        help='Show the compilation progress')
    parser.add_argument('-c', action='store_true',
                        help='compile and assemble, but do not link')
    parser.add_argument('-commands', help='print command lines executed',
                        action='store_true')
    parser.add_argument('-v', '--version', dest='version', action='store_true',
                        help='print version info')

    arguments, argv = parser.parse_known_args()

    if argv:
        arguments.unknown_args = filter(lambda x: x[0] == '-', argv)
        arguments.files = arguments.files + filter(lambda x: x[0] != '-', argv)
    else:
        arguments.unknown_args = []

    return arguments


def compile_no_link(args, flags):
    """

    :param args:
    :param flags:
    :return:
    """
    includes = ['-include' + x for x in args.extra_includes] + \
               ['-I' + x for x in args.incdirs]

    commandLine = [pprof.clang(), '-c', '-emit-llvm'] + includes
    commandLine = commandLine + args.unknown_args + args.files

    out = ''
    if args.output:
        out = args.output
    elif args.c and len(args.files) == 1:
        out = os.path.splitext(args.files[0])[0]
        out = os.path.basename(out) + '.o'

    if out:
        commandLine = commandLine + ['-o', out]
        pprof.log_exec(
            args, commandLine, 'Creating BITCODE (unoptimized)', False)

        commandLine = ['opt', out, '-o', out]
        pprof.log_exec(args, commandLine, 'Creating bitcode', False)
    return args.output


def print_version(args):
    """

    :param args:
    """
    pprof.log_exec(args, [pprof.GCC, '--version'],
                   'Version check pass-through', False)


def main():
    """


    :return:
    """
    args = parseArguments()

    # PWN configure scripts:
    if (args.version):
        return print_version(args)

    # Fortran
    if sys.argv[0].endswith('fortran'):
        pprof.FORTRAN = True

    # C or C++?
    if sys.argv[0].endswith('++'):
        pprof.GCC = 'g++'
        pprof.CLANG = 'clang++'

    if args.c:
        compile_no_link(args, [])
    else:
        ir = pprof.link_ir(args, None)
        pprof.link(ir, args)


if __name__ == '__main__':
    main()

#    if pprof.FORTRAN:
#        commandLine = ['gfortran', '-fplugin=/usr/lib64/llvm/dragonegg.so',
#                       '-fplugin-arg-dragonegg-emit-ir',
#                       '-S'] + args.unknown_args + args.files
