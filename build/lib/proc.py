# Copyright (c) 2026 Christian Relf. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Subprocess and console helpers shared by the Dandelion build scripts."""

import shutil
import subprocess
import sys


class CommandError(Exception):
  """Raised when a subprocess exits non-zero and the caller wanted success."""


def _supports_color():
  return sys.stdout.isatty()


def _paint(code, text):
  if not _supports_color():
    return text
  return '\033[%sm%s\033[0m' % (code, text)


def info(message):
  print('%s %s' % (_paint('36;1', '==>'), message), flush=True)


def warn(message):
  print('%s %s' % (_paint('33;1', 'warning:'), message), flush=True)


def error(message):
  print('%s %s' % (_paint('31;1', 'error:'), message), file=sys.stderr,
        flush=True)


def _needs_shell(program):
  """Returns True if `program` can only be launched through a shell.

  The depot_tools entry points are .bat files, which CreateProcess cannot
  execute directly. Everything else is launched without a shell so that
  arguments containing spaces or cmd.exe metacharacters are passed through
  verbatim rather than being re-parsed.
  """
  if sys.platform != 'win32':
    return False
  resolved = shutil.which(program)
  return resolved is None or resolved.lower().endswith(('.bat', '.cmd'))


def run(args, cwd=None, check=True, capture=False, env=None):
  """Runs a command, streaming output unless `capture` is set."""
  printable = ' '.join(args)
  if not capture:
    info(printable)

  completed = subprocess.run(
      args,
      cwd=cwd,
      env=env,
      shell=_needs_shell(args[0]),
      stdout=subprocess.PIPE if capture else None,
      stderr=subprocess.PIPE if capture else None,
      text=True)

  if check and completed.returncode != 0:
    if capture and completed.stderr:
      error(completed.stderr.strip())
    raise CommandError('%s exited with %d' % (printable, completed.returncode))
  return completed


def git(args, cwd, check=True, capture=True):
  """Runs a git command, capturing stdout by default."""
  return run(['git'] + args, cwd=cwd, check=check, capture=capture)


def git_output(args, cwd):
  """Runs a git command and returns its stdout with trailing newlines removed."""
  return git(args, cwd=cwd).stdout.rstrip('\n')
