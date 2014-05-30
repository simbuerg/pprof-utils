#!/usr/bin/env python2.7
import argparse
import subprocess
import tempfile
import os
import os.path
import sys
import traceback

PREFIX = '[PP] '
GCC = 'gcc'
CLANG = 'clang'
PLUGIN = os.environ['PPROF_LLVMGOLD']

if "PPROF_LLVM_BINARY_PREFIX" in os.environ:
    LLVM_BINARY_PREFIX = os.environ['PPROF_LLVM_BINARY_PREFIX']
else:
    LLVM_BINARY_PREFIX = ""

FORTRAN = False

LD_PATH = []
LD_FLAGS = []

def clang():
  global CLANG
  global LLVM_BINARY_PREFIX

  clng = os.path.join(LLVM_BINARY_PREFIX, CLANG)
  # C or C++?
  if sys.argv[0].endswith('++') or '-cpp' in sys.argv:
    clng = os.path.join(LLVM_BINARY_PREFIX, 'clang++')

  return clng

def gcc():
  global GCC

  gcc = GCC

  # C or C++?
  if sys.argv[0].endswith('++') or '-cpp' in sys.argv:
    gcc = 'g++'

  return gcc

clean_log = True
# Execute process with nice pretty printing of our debugging outputs.
#
def log_exec(args, commandLine, msg, failOnErr = True, toFile = True):
  global clean_log
  level = len(traceback.format_stack())
  indent = '  ' * (level-5)

  if args.prg:
    print >> sys.stderr, indent + '\033[1;31m[ '+ msg +' ]\033[1;m'

  if args.commands:
    print >> sys.stderr, indent + '\033[1;36m' + ' '.join(commandLine) + '\033[1;m'

  if toFile:
    fn = getOutput(args) + '.pprof'
    if clean_log:
      f = open(fn, 'w')
      clean_log = False
    else:
      f = open(fn, 'a')

    f.write(' '.join(commandLine))
    f.write('\n')
    f.close()

  exit = subprocess.call(commandLine)
  if exit:
    print >> sys.stderr, indent + '\033[1;36m' + msg + ' FAILED. This command did not work:\033[1;m'
    print >> sys.stderr, indent + '\033[1;36m' + ' '.join(commandLine) + '\033[1;m'

    if failOnErr:
      sys.exit(exit)

    margv = sys.argv
    margv[0] = gcc()
    commandLine = margv
    exit = subprocess.call(commandLine)

  return exit

# Preprocess the programm such that as many optimization opportunities
# as possible are exposed.
def optimize_ir(file, args):
  preoptFile = os.path.splitext(file)[0] + '.opt'

  # Sanity check our env
  if not 'LIBPOLLY' in os.environ:
    sys.exit('Polly library not provided. Please set LIBPOLLY environment ' + \
             'variable to the LLVMPolly.so file')
  polly = os.environ['LIBPOLLY']

  commandLine = [clang(), '-Xclang', '-load', '-Xclang', polly, '-O0', '-mllvm',
                          '-polly', '-S', '-emit-llvm'] + [file, '-o', preoptFile]
  exit = log_exec(args, commandLine, 'Preoptimizing to expose optimization opportunities', False)

  return preoptFile

def link_ir(args, flags):
  outFile = getOutput(args)
  out = os.path.splitext(outFile)[0] + '.bc'
  global LD_PATH

  lflags = ['-l' + x for x in args.libraries] + LD_FLAGS
  lpath  = ['-L' + x for x in args.librarypath] + LD_PATH

  # Sanity check our env
  if not 'PPROF_LLVMGOLD' in os.environ:
    sys.exit('LLVMGold library not provided. Please set PPROF_LLVMGOLD' + \
             'environment variable to the LLVMGold.so file')
  goldplugin = os.environ['PPROF_LLVMGOLD']

  # Order of linker flags MATTERS!!! don't swap args.files & args.unknown_args
  commandLine = [clang() , '-Xclang', '-emit-llvm-bc', '-Wl,-plugin,' + \
                 goldplugin+',-plugin-opt,emit-llvm', '-o', out] + \
                 args.files + lflags + lpath + \
                 args.unknown_args + LD_PATH + flags
  log_exec(args, commandLine, 'Linking BITCODE (unoptimized)')

  return out

def link_ir_fortran(args, flags):
  outFile = getOutput(args)
  out = os.path.splitext(outFile)[0] + '.bc'
  global LD_PATH
  global LLVM_BINARY_PREFIX

  lflags = ['-l' + x for x in args.libraries] + LD_FLAGS
  lpath = ['-L' + x for x in args.librarypath] + LD_PATH

  # Sanity check our env
  if not 'PPROF_LLVMGOLD' in os.environ:
    sys.exit('LLVMGold library not provided. Please set PPROF_LLVMGOLD' + \
             'environment variable to the LLVMGold.so file')
  goldplugin = os.environ['PPROF_LLVMGOLD']

  # Order of linker flags MATTERS!!! don't swap args.files & args.unknown_args
  commandLine = [clang() , '-Wl,-plugin,'+goldplugin+',-plugin-opt,emit-llvm',
                 '-o', out] + args.files + lflags + lpath + \
                 args.unknown_args + LD_PATH + flags
  log_exec(args, commandLine, 'Linking human-readable bitcode (unoptimized)')

  commandLine = [os.path.join(LLVM_BINARY_PREFIX, 'opt'), out, '-o', out]
  log_exec(args, commandLine, 'Creating bitcode')
  return out


def getOutput(args):
  if args.output and len(args.output) > 0:
    outFile = args.output
  else:
    outFile = 'a.out'

  return outFile

def link(ir, args, flags):
  lflags = ['-l' + x for x in args.libraries] + LD_FLAGS
  lpath = ['-L' + x for x in args.librarypath] + LD_PATH

  out = getOutput(args)
  assembly = ir + '.s'

  commandLine = ['llc', '-O0', ir, '-o', assembly]
  if args.fPIC or args.fpic:
    commandLine += ['-relocation-model=pic']

  log_exec(args, commandLine, 'Generating assembly')

  commandLine = [gcc(), assembly, '-o', out] + \
                 args.unknown_args + lflags + lpath + LD_PATH

  log_exec(args, commandLine, 'Generating final output')
  return args.output

def link_fortran(ir, args, flags):
  global LD_PATH

  lflags = ['-l' + x for x in args.libraries] + LD_FLAGS
  lpath = ['-L' + x for x in args.librarypath] + LD_PATH

  out = getOutput(args)
  assembly = ir + '.s'
  commandLine = ['llc', ir]
  log_exec(args, commandLine, 'Generating assembly')

  commandLine = ['gfortran', assembly, '-o', out] + lflags + lpath + LD_PATH

  log_exec(args, commandLine, 'Generating final output')
  return args.output
