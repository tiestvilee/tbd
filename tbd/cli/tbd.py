# -*- coding: utf-8 -*-
# Gitless - a version control system built on top of Git
# Licensed under MIT

"""tbd - Main Gitless's command. Dispatcher to the other cmds."""


from __future__ import unicode_literals

import sys
import argparse
import traceback
import pygit2

if sys.platform != 'win32':
  from sh import ErrorReturnCode
else:
  from pbs import ErrorReturnCode

from clint.textui import colored

from tbd import core

from . import (
    tbd_track, tbd_untrack, tbd_status, tbd_diff, tbd_commit, tbd_branch, tbd_tag,
    tbd_checkout, tbd_merge, tbd_resolve, tbd_fuse, tbd_remote, tbd_publish,
    tbd_switch, tbd_init, tbd_history)
from . import pprint


SUCCESS = 0
ERRORS_FOUND = 1
# 2 is used by argparse to indicate cmd syntax errors.
INTERNAL_ERROR = 3
NOT_IN_TBD_REPO = 4

__version__ = '0.8.6'
URL = 'http://tbd.com'


repo = None
try:
  repo = core.Repository()
  try:
    colored.DISABLE_COLOR = not repo.config.get_bool('color.ui')
  except pygit2.GitError:
    colored.DISABLE_COLOR = (
        repo.config['color.ui'] in ['no', 'never'])
except (core.NotInRepoError, KeyError):
  pass


def print_help(parser):
  """print help for humans"""
  print(parser.description)
  print('\ncommands:\n')

  # https://stackoverflow.com/questions/20094215/argparse-subparser-monolithic-help-output
  # retrieve subparsers from parser
  subparsers_actions = [
      action for action in parser._actions
      if isinstance(action, argparse._SubParsersAction)]
  # there will probably only be one subparser_action,
  # but better safe than sorry
  for subparsers_action in subparsers_actions:
      # get all subparsers and print help
      for choice in subparsers_action._choices_actions:
          print('    {:<19} {}'.format(choice.dest, choice.help))

def main():
  parser = argparse.ArgumentParser(
      description=(
          'Gitless: a version control system built on top of Git.\nMore info, '
          'downloads and documentation at {0}'.format(URL)),
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument(
      '--version', action='version', version=(
         'TBD Version: {0}\nYou can check if there\'s a new version of Gitless '
         'available at {1}'.format(__version__, URL)))
  subparsers = parser.add_subparsers(title='subcommands', dest='subcmd_name')
  subparsers.required = True

  sub_cmds = [
      tbd_track, tbd_untrack, tbd_status, tbd_diff, tbd_commit, tbd_branch, tbd_tag,
      tbd_checkout, tbd_merge, tbd_resolve, tbd_fuse, tbd_remote, tbd_publish,
      tbd_switch, tbd_init, tbd_history]
  for sub_cmd in sub_cmds:
    sub_cmd.parser(subparsers, repo)

  if len(sys.argv) == 1:
    print_help(parser)
    return SUCCESS

  args = parser.parse_args()
  try:
    if args.subcmd_name != 'init' and not repo:
      raise core.NotInRepoError('You are not in a Gitless\'s repository')

    return SUCCESS if args.func(args, repo) else ERRORS_FOUND
  except KeyboardInterrupt:
    pprint.puts('\n')
    pprint.msg('Keyboard interrupt detected, operation aborted')
    return SUCCESS
  except core.NotInRepoError as e:
    pprint.err(e)
    pprint.err_exp('do tbd init to turn this directory into an empty repository')
    pprint.err_exp('do tbd init remote_repo to clone an existing repository')
    return NOT_IN_TBD_REPO
  except (ValueError, pygit2.GitError, core.TbdError) as e:
    pprint.err(e)
    return ERRORS_FOUND
  except ErrorReturnCode as e:
    pprint.err(e.stderr)
    return ERRORS_FOUND
  except:
    pprint.err('Some internal error occurred')
    pprint.err_exp(
        'If you want to help, see {0} for info on how to report bugs and '
        'include the following information:\n\n{1}\n\n{2}'.format(
            URL, __version__, traceback.format_exc()))
    return INTERNAL_ERROR
