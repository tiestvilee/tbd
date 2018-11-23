# -*- coding: utf-8 -*-
# Gitless - a version control system built on top of Git
# Licensed under MIT

"""End-to-end test."""


from __future__ import unicode_literals

import logging
import os
import re
import time

import sys
if sys.platform != 'win32':
  from sh import ErrorReturnCode, tbd, git
else:
  from pbs import ErrorReturnCode, Command
  tbd = Command('tbd')
  git = Command('git')


from tbd.tests import utils

try:
  text = unicode
except NameError:
  text = str


class TestEndToEnd(utils.TestBase):

  def setUp(self):
    super(TestEndToEnd, self).setUp('tbd-e2e-test')
    tbd.init()
    # Disable colored output so that we don't need to worry about ANSI escape
    # codes
    git.config('color.ui', False)
    # Disable paging so that we don't have to use sh's _tty_out option, which is
    # not available on pbs
    if sys.platform != 'win32':
      git.config('core.pager', 'cat')
    else:
      # On Windows, we need to call 'type' through cmd.exe (with 'cmd'). The /C
      # is so that the command window gets closed after 'type' finishes
      git.config('core.pager', 'cmd /C type')
    utils.set_test_config()


class TestNotInRepo(utils.TestBase):

  def setUp(self):
    super(TestNotInRepo, self).setUp('tbd-e2e-test')

  def test_not_in_repo(self):
    def assert_not_in_repo(*cmds):
      for cmd in cmds:
        self.assertRaisesRegexp(
            ErrorReturnCode, 'not in a Gitless\'s repository', cmd)

    assert_not_in_repo(
      tbd.status, tbd.diff, tbd.commit, tbd.branch, tbd.merge, tbd.fuse, tbd.remote,
      tbd.publish, tbd.history)


class TestBasic(TestEndToEnd):

  def test_basic_functionality(self):
    utils.write_file('file1', 'Contents of file1')
    # Track
    tbd.track('file1')
    self.assertRaises(ErrorReturnCode, tbd.track, 'file1')
    self.assertRaises(ErrorReturnCode, tbd.track, 'non-existent')
    # Untrack
    tbd.untrack('file1')
    self.assertRaises(ErrorReturnCode, tbd.untrack, 'file1')
    self.assertRaises(ErrorReturnCode, tbd.untrack, 'non-existent')
    # Commit
    tbd.track('file1')
    tbd.commit(m='file1 commit')
    self.assertRaises(ErrorReturnCode, tbd.commit, m='nothing to commit')
    # History
    if 'file1 commit' not in utils.stdout(tbd.history()):
      self.fail('Commit didn\'t appear in history')
    # Branch
    # Make some changes to file1 and branch out
    utils.write_file('file1', 'New contents of file1')
    tbd.branch(c='branch1')
    tbd.switch('branch1')
    if 'New' in utils.read_file('file1'):
      self.fail('Branch not independent!')
    # Switch back to master branch, check that contents are the same as before.
    tbd.switch('master')
    if 'New' not in utils.read_file('file1'):
      self.fail('Branch not independent!')
    out = utils.stdout(tbd.branch())
    if '* master' not in out:
      self.fail('Branch status output wrong: {0}'.format(out))
    if 'branch1' not in out:
      self.fail('Branch status output wrong: {0}'.format(out))

    tbd.branch(c='branch2')
    tbd.branch(c='branch-conflict1')
    tbd.branch(c='branch-conflict2')
    tbd.commit(m='New contents commit')

    # Fuse
    tbd.switch('branch1')
    self.assertRaises(ErrorReturnCode, tbd.fuse)  # no upstream set
    try:
      tbd.fuse('master')
    except ErrorReturnCode as e:
      self.fail(utils.stderr(e))
    out = utils.stdout(tbd.history())
    if 'file1 commit' not in out:
      self.fail(out)

    # Merge
    tbd.switch('branch2')
    self.assertRaises(ErrorReturnCode, tbd.merge)  # no upstream set
    tbd.merge('master')
    out = utils.stdout(tbd.history())
    if 'file1 commit' not in out:
      self.fail(out)

    # Conflicting fuse
    tbd.switch('branch-conflict1')
    utils.write_file('file1', 'Conflicting changes to file1')
    tbd.commit(m='changes in branch-conflict1')
    err = utils.stderr(tbd.fuse('master', _ok_code=[1]))
    if 'conflict' not in err:
      self.fail(err)
    out = utils.stdout(tbd.status())
    if 'file1 (with conflicts)' not in out:
      self.fail(out)

    # Try aborting
    tbd.fuse('--abort')
    out = utils.stdout(tbd.status())
    if 'file1' in out:
      self.fail(out)

    # Ok, now let's fix the conflicts
    err = utils.stderr(tbd.fuse('master', _ok_code=[1]))
    if 'conflict' not in err:
      self.fail(err)
    out = utils.stdout(tbd.status())
    if 'file1 (with conflicts)' not in out:
      self.fail(out)

    utils.write_file('file1', 'Fixed conflicts!')
    self.assertRaises(ErrorReturnCode, tbd.commit, m='resolve not called')
    self.assertRaises(ErrorReturnCode, tbd.resolve, 'non-existent')
    tbd.resolve('file1')
    tbd.commit(m='fixed conflicts')


class TestCommit(TestEndToEnd):

  TRACKED_FP = 'file1'
  DIR_TRACKED_FP = 'dir/dir_file'
  UNTRACKED_FP = 'file2'
  FPS = [TRACKED_FP, DIR_TRACKED_FP, UNTRACKED_FP]
  DIR = 'dir'

  def setUp(self):
    super(TestCommit, self).setUp()
    utils.write_file(self.TRACKED_FP)
    utils.write_file(self.DIR_TRACKED_FP)
    utils.write_file(self.UNTRACKED_FP)
    tbd.track(self.TRACKED_FP, self.DIR_TRACKED_FP)

  def test_commit(self):
    tbd.commit(m='msg')
    self.__assert_commit(self.TRACKED_FP, self.DIR_TRACKED_FP)

  def test_commit_relative(self):
    os.chdir(self.DIR)
    tbd.commit(m='msg')
    self.__assert_commit(self.TRACKED_FP, self.DIR_TRACKED_FP)

  def test_commit_only(self):
    tbd.commit(self.TRACKED_FP, m="msg")
    self.__assert_commit(self.TRACKED_FP)

  def test_commit_only_relative(self):
    os.chdir(self.DIR)
    self.assertRaises(ErrorReturnCode, tbd.commit, self.TRACKED_FP, "-m='msg'")
    tbd.commit('../' + self.TRACKED_FP, m='msg')
    self.__assert_commit(self.TRACKED_FP)

  def test_commit_only_untrack(self):
    tbd.commit("-m='msg'", self.UNTRACKED_FP)
    self.__assert_commit(self.UNTRACKED_FP)

  def test_commit_only_untrack_relative(self):
    os.chdir(self.DIR)
    self.assertRaises(ErrorReturnCode, tbd.commit, self.UNTRACKED_FP, m='msg')
    tbd.commit('../' + self.UNTRACKED_FP, m='msg')
    self.__assert_commit(self.UNTRACKED_FP)

  def test_commit_include(self):
    tbd.commit("-m='msg'", include=self.UNTRACKED_FP)
    self.__assert_commit(
        self.TRACKED_FP, self.DIR_TRACKED_FP, self.UNTRACKED_FP)

  def test_commit_exclude_include(self):
    tbd.commit("-m='msg'", include=self.UNTRACKED_FP, exclude=self.TRACKED_FP)
    self.__assert_commit(self.UNTRACKED_FP, self.DIR_TRACKED_FP)

  def test_commit_no_files(self):
    self.assertRaises(
        ErrorReturnCode, tbd.commit, '--exclude',
        self.TRACKED_FP, self.DIR_TRACKED_FP, m='msg')
    self.assertRaises(ErrorReturnCode, tbd.commit, 'non-existent', m='msg')
    self.assertRaises(
        ErrorReturnCode, tbd.commit, m='msg', exclude='non-existent')
    self.assertRaises(
        ErrorReturnCode, tbd.commit, m='msg', include='non-existent')

  def test_commit_dir(self):
    fp = 'dir/f'
    utils.write_file(fp)
    tbd.commit(fp, m='msg')
    self.__assert_commit('dir/f')

  def __assert_commit(self, *expected_committed):
    h = utils.stdout(tbd.history(v=True))
    for fp in expected_committed:
      if fp not in h:
        self.fail('{0} was apparently not committed!'.format(fp))
    expected_not_committed = [
        fp for fp in self.FPS if fp not in expected_committed]
    for fp in expected_not_committed:
      if fp in h:
        self.fail('{0} was apparently committed!'.format(fp))


class TestStatus(TestEndToEnd):

  DIR = 'dir'
  TRACKED_DIR_FP = os.path.join('dir', 'file1')
  UNTRACKED_DIR_FP = os.path.join('dir', 'file2')

  def setUp(self):
    super(TestStatus, self).setUp()
    utils.write_file(self.TRACKED_DIR_FP)
    utils.write_file(self.UNTRACKED_DIR_FP)
    tbd.commit(self.TRACKED_DIR_FP, m='commit')

  def test_status_relative(self):
    utils.write_file(self.TRACKED_DIR_FP, contents='some modifications')
    st = utils.stdout(tbd.status())
    if self.TRACKED_DIR_FP not in st:
      self.fail()
    if self.UNTRACKED_DIR_FP not in st:
      self.fail()

    os.chdir(self.DIR)

    st = utils.stdout(tbd.status())
    rel_tracked = os.path.relpath(self.TRACKED_DIR_FP, self.DIR)
    rel_untracked = os.path.relpath(self.UNTRACKED_DIR_FP, self.DIR)
    if (self.TRACKED_DIR_FP in st) or (rel_tracked not in st):
      self.fail()
    if (self.UNTRACKED_DIR_FP in st) or (rel_untracked not in st):
      self.fail()


class TestBranch(TestEndToEnd):

  BRANCH_1 = 'branch1'
  BRANCH_2 = 'branch2'

  def setUp(self):
    super(TestBranch, self).setUp()
    utils.write_file('f')
    tbd.commit('f', m='commit')

  def test_create(self):
    tbd.branch(c=self.BRANCH_1)
    self.assertRaises(ErrorReturnCode, tbd.branch, c=self.BRANCH_1)
    self.assertRaises(ErrorReturnCode, tbd.branch, c='evil*named*branch')
    if self.BRANCH_1 not in utils.stdout(tbd.branch()):
      self.fail()

  def test_remove(self):
    tbd.branch(c=self.BRANCH_1)
    tbd.switch(self.BRANCH_1)
    self.assertRaises(ErrorReturnCode, tbd.branch, d=self.BRANCH_1, _in='y')
    tbd.branch(c=self.BRANCH_2)
    tbd.switch(self.BRANCH_2)
    tbd.branch(d=self.BRANCH_1, _in='n')
    tbd.branch(d=self.BRANCH_1, _in='y')
    if self.BRANCH_1 in utils.stdout(tbd.branch()):
      self.fail()

  def test_upstream(self):
    self.assertRaises(ErrorReturnCode, tbd.branch, '-uu')
    self.assertRaises(ErrorReturnCode, tbd.branch, '-su', 'non-existent')
    self.assertRaises(
        ErrorReturnCode, tbd.branch, '-su', 'non-existent/non-existent')

  def test_list(self):
    tbd.branch(c=self.BRANCH_1)
    tbd.branch(c=self.BRANCH_2)
    branch_out = utils.stdout(tbd.branch())
    self.assertTrue(
        branch_out.find(self.BRANCH_1) < branch_out.find(self.BRANCH_2))


class TestTag(TestEndToEnd):

  TAG_1 = 'tag1'
  TAG_2 = 'tag2'

  def setUp(self):
    super(TestTag, self).setUp()
    utils.write_file('f')
    tbd.commit('f', m='commit')

  def test_create(self):
    tbd.tag(c=self.TAG_1)
    self.assertRaises(ErrorReturnCode, tbd.tag, c=self.TAG_1)
    self.assertRaises(ErrorReturnCode, tbd.tag, c='evil*named*tag')
    if self.TAG_1 not in utils.stdout(tbd.tag()):
      self.fail()

  def test_remove(self):
    tbd.tag(c=self.TAG_1)
    tbd.tag(d=self.TAG_1, _in='n')
    tbd.tag(d=self.TAG_1, _in='y')
    if self.TAG_1 in utils.stdout(tbd.tag()):
      self.fail()

  def test_list(self):
    tbd.tag(c=self.TAG_1)
    tbd.tag(c=self.TAG_2)
    tag_out = utils.stdout(tbd.tag())
    self.assertTrue(
        tag_out.find(self.TAG_1) < tag_out.find(self.TAG_2))


class TestDiffFile(TestEndToEnd):

  TRACKED_FP = 't_fp'
  DIR_TRACKED_FP = os.path.join('dir', 't_fp')
  UNTRACKED_FP = 'u_fp'
  DIR = 'dir'

  def setUp(self):
    super(TestDiffFile, self).setUp()
    utils.write_file(self.TRACKED_FP)
    utils.write_file(self.DIR_TRACKED_FP)
    tbd.commit(self.TRACKED_FP, self.DIR_TRACKED_FP, m='commit')
    utils.write_file(self.UNTRACKED_FP)

  def test_empty_diff(self):
    if 'No files to diff' not in utils.stdout(tbd.diff()):
      self.fail()

  def test_diff_nonexistent_fp(self):
    err = utils.stderr(tbd.diff('file', _ok_code=[1]))
    if 'doesn\'t exist' not in err:
      self.fail()

  def test_basic_diff(self):
    utils.write_file(self.TRACKED_FP, contents='contents')
    out1 = utils.stdout(tbd.diff())
    if '+contents' not in out1:
      self.fail()
    out2 = utils.stdout(tbd.diff(self.TRACKED_FP))
    if '+contents' not in out2:
      self.fail()
    self.assertEqual(out1, out2)

  def test_basic_diff_relative(self):
    utils.write_file(self.TRACKED_FP, contents='contents_tracked')
    utils.write_file(self.DIR_TRACKED_FP, contents='contents_dir_tracked')
    os.chdir(self.DIR)
    out1 = utils.stdout(tbd.diff())
    if '+contents_tracked' not in out1:
      self.fail()
    if '+contents_dir_tracked' not in out1:
      self.fail()
    rel_dir_tracked_fp = os.path.relpath(self.DIR_TRACKED_FP, self.DIR)
    out2 = utils.stdout(tbd.diff(rel_dir_tracked_fp))
    if '+contents_dir_tracked' not in out2:
      self.fail()

  def test_diff_dir(self):
    fp = 'dir/dir/f'
    utils.write_file(fp, contents='contents')
    out = utils.stdout(tbd.diff(fp))
    if '+contents' not in out:
      self.fail()

  def test_diff_non_ascii(self):
    if sys.platform == 'win32':
      # Skip this test on Windows until we fix Unicode support
      return
    contents = '’◕‿◕’©Ä☺’ಠ_ಠ’'
    utils.write_file(self.TRACKED_FP, contents=contents)
    out1 = utils.stdout(tbd.diff())
    if '+' + contents not in out1:
      self.fail('out is ' + out1)
    out2 = utils.stdout(tbd.diff(self.TRACKED_FP))
    if '+' + contents not in out2:
      self.fail('out is ' + out2)
    self.assertEqual(out1, out2)


class TestOp(TestEndToEnd):

  COMMITS_NUMBER = 4
  OTHER = 'other'
  MASTER_FILE = 'master_file'
  OTHER_FILE = 'other_file'

  def setUp(self):
    super(TestOp, self).setUp()

    self.commits = {}
    def create_commits(branch_name, fp):
      self.commits[branch_name] = []
      utils.append_to_file(fp, contents='contents {0}\n'.format(0))
      out = utils.stdout(tbd.commit(m='ci 0 in {0}'.format(branch_name), inc=fp))
      self.commits[branch_name].append(
          re.search(r'Commit Id: (\S*)', out, re.UNICODE).group(1))
      for i in range(1, self.COMMITS_NUMBER):
        utils.append_to_file(fp, contents='contents {0}\n'.format(i))
        out = utils.stdout(tbd.commit(m='ci {0} in {1}'.format(i, branch_name)))
        self.commits[branch_name].append(
            re.search(r'Commit Id: (\S*)', out, re.UNICODE).group(1))

    tbd.branch(c=self.OTHER)
    create_commits('master', self.MASTER_FILE)
    tbd.switch(self.OTHER)
    create_commits(self.OTHER, self.OTHER_FILE)
    tbd.switch('master')


class TestFuse(TestOp):

  def __assert_history(self, expected):
    out = utils.stdout(tbd.history())
    cids = list(reversed(re.findall(r'ci (.*) in (\S*)', out, re.UNICODE)))
    self.assertItemsEqual(
        cids, expected, 'cids is ' + text(cids) + ' exp ' + text(expected))

    st_out = utils.stdout(tbd.status())
    self.assertFalse('fuse' in st_out)

  def __build(self, branch_name, cids=None):
    if not cids:
      cids = range(self.COMMITS_NUMBER)
    return [(text(ci), branch_name) for ci in cids]

  def test_basic(self):
    tbd.fuse(self.OTHER)
    self.__assert_history(self.__build(self.OTHER) + self.__build('master'))

  def test_only_errors(self):
    self.assertRaises(ErrorReturnCode, tbd.fuse, self.OTHER, o='non-existent-id')
    self.assertRaises(
        ErrorReturnCode, tbd.fuse, self.OTHER, o=self.commits['master'][1])

  def test_only_one(self):
    tbd.fuse(self.OTHER, o=self.commits[self.OTHER][0])
    self.__assert_history(
        self.__build(self.OTHER, cids=[0]) + self.__build('master'))

  def test_only_some(self):
    tbd.fuse(self.OTHER, '-o', self.commits[self.OTHER][:2])
    self.__assert_history(
        self.__build(self.OTHER, [0, 1]) + self.__build('master'))

  def test_exclude_errors(self):
    self.assertRaises(ErrorReturnCode, tbd.fuse, self.OTHER, e='non-existent-id')
    self.assertRaises(
        ErrorReturnCode, tbd.fuse, self.OTHER, e=self.commits['master'][1])

  def test_exclude_one(self):
    last_ci = self.COMMITS_NUMBER - 1
    tbd.fuse(self.OTHER, e=self.commits[self.OTHER][last_ci])
    self.__assert_history(
        self.__build(self.OTHER, range(0, last_ci)) + self.__build('master'))

  def test_exclude_some(self):
    tbd.fuse(self.OTHER, '-e', self.commits[self.OTHER][1:])
    self.__assert_history(
        self.__build(self.OTHER, cids=[0]) + self.__build('master'))

  def test_ip_dp(self):
    tbd.fuse(self.OTHER, insertion_point='dp')
    self.__assert_history(self.__build(self.OTHER) + self.__build('master'))

  def test_ip_head(self):
    tbd.fuse(self.OTHER, insertion_point='HEAD')
    self.__assert_history(self.__build('master') + self.__build(self.OTHER))

  def test_ip_commit(self):
    tbd.fuse(self.OTHER, insertion_point=self.commits['master'][1])
    self.__assert_history(
        self.__build('master', [0, 1]) + self.__build(self.OTHER) +
        self.__build('master', range(2, self.COMMITS_NUMBER)))

  def test_conflicts(self):
    def trigger_conflicts():
      self.assertRaisesRegexp(
          ErrorReturnCode, 'conflicts', tbd.fuse,
          self.OTHER, e=self.commits[self.OTHER][0])

    # Abort
    trigger_conflicts()
    tbd.fuse('-a')
    self.__assert_history(self.__build('master'))

    # Fix conflicts
    trigger_conflicts()
    tbd.resolve(self.OTHER_FILE)
    tbd.commit(m='ci 1 in other')
    self.__assert_history(
        self.__build(self.OTHER, range(1, self.COMMITS_NUMBER)) +
        self.__build('master'))

  def test_conflicts_switch(self):
    tbd.switch('other')
    utils.write_file(self.OTHER_FILE, contents='uncommitted')
    tbd.switch('master')
    try:
      tbd.fuse(self.OTHER, e=self.commits[self.OTHER][0])
      self.fail()
    except ErrorReturnCode:
      pass

    # Switch
    tbd.switch('other')
    self.__assert_history(self.__build('other'))
    st_out = utils.stdout(tbd.status())
    self.assertTrue('fuse' not in st_out)
    self.assertTrue('conflict' not in st_out)

    tbd.switch('master')
    st_out = utils.stdout(tbd.status())
    self.assertTrue('fuse' in st_out)
    self.assertTrue('conflict' in st_out)

    # Check that we are able to complete the fuse after switch
    tbd.resolve(self.OTHER_FILE)
    tbd.commit(m='ci 1 in other')
    self.__assert_history(
        self.__build(self.OTHER, range(1, self.COMMITS_NUMBER)) +
        self.__build('master'))

    tbd.switch('other')
    self.assertEqual('uncommitted', utils.read_file(self.OTHER_FILE))

  def test_conflicts_multiple(self):
    tbd.branch(c='tmp', divergent_point='HEAD~2')
    tbd.switch('tmp')
    utils.append_to_file(self.MASTER_FILE, contents='conflict')
    tbd.commit(m='will conflict 0')
    utils.append_to_file(self.MASTER_FILE, contents='conflict')
    tbd.commit(m='will conflict 1')

    self.assertRaisesRegexp(ErrorReturnCode, 'conflicts', tbd.fuse, 'master')
    tbd.resolve(self.MASTER_FILE)
    self.assertRaisesRegexp(
        ErrorReturnCode, 'conflicts', tbd.commit, m='ci 0 in tmp')
    tbd.resolve(self.MASTER_FILE)
    tbd.commit(m='ci 1 in tmp')  # this one should finalize the fuse

    self.__assert_history(
        self.__build('master') + self.__build('tmp', range(2)))

  def test_conflicts_multiple_uncommitted_changes(self):
    tbd.branch(c='tmp', divergent_point='HEAD~2')
    tbd.switch('tmp')
    utils.append_to_file(self.MASTER_FILE, contents='conflict')
    tbd.commit(m='will conflict 0')
    utils.append_to_file(self.MASTER_FILE, contents='conflict')
    tbd.commit(m='will conflict 1')
    utils.write_file(self.MASTER_FILE, contents='uncommitted')

    self.assertRaisesRegexp(ErrorReturnCode, 'conflicts', tbd.fuse, 'master')
    tbd.resolve(self.MASTER_FILE)
    self.assertRaisesRegexp(
        ErrorReturnCode, 'conflicts', tbd.commit, m='ci 0 in tmp')
    tbd.resolve(self.MASTER_FILE)
    self.assertRaisesRegexp(
        ErrorReturnCode, 'failed to apply', tbd.commit, m='ci 1 in tmp')

    self.__assert_history(
        self.__build('master') + self.__build('tmp', range(2)))
    self.assertTrue('Stashed' in utils.read_file(self.MASTER_FILE))

  def test_nothing_to_fuse(self):
    self.assertRaisesRegexp(
        ErrorReturnCode, 'No commits to fuse', tbd.fuse,
        self.OTHER, '-e', *self.commits[self.OTHER])

  def test_ff(self):
    tbd.branch(c='tmp', divergent_point='HEAD~2')
    tbd.switch('tmp')

    tbd.fuse('master')
    self.__assert_history(self.__build('master'))

  def test_ff_ip_head(self):
    tbd.branch(c='tmp', divergent_point='HEAD~2')
    tbd.switch('tmp')

    tbd.fuse('master', insertion_point='HEAD')
    self.__assert_history(self.__build('master'))

  def test_uncommitted_changes(self):
    utils.write_file(self.MASTER_FILE, contents='uncommitted')
    utils.write_file('master_untracked', contents='uncommitted')
    tbd.fuse(self.OTHER)
    self.assertEqual('uncommitted', utils.read_file(self.MASTER_FILE))
    self.assertEqual('uncommitted', utils.read_file('master_untracked'))

  def test_uncommitted_tracked_changes_that_conflict(self):
    tbd.branch(c='tmp', divergent_point='HEAD~1')
    tbd.switch('tmp')
    utils.write_file(self.MASTER_FILE, contents='uncommitted')
    self.assertRaisesRegexp(
        ErrorReturnCode, 'failed to apply', tbd.fuse,
        'master', insertion_point='HEAD')
    contents = utils.read_file(self.MASTER_FILE)
    self.assertTrue('uncommitted' in contents)
    self.assertTrue('contents 2' in contents)

  def test_uncommitted_tracked_changes_that_conflict_append(self):
    tbd.branch(c='tmp', divergent_point='HEAD~1')
    tbd.switch('tmp')
    utils.append_to_file(self.MASTER_FILE, contents='uncommitted')
    self.assertRaisesRegexp(
        ErrorReturnCode, 'failed to apply', tbd.fuse,
        'master', insertion_point='HEAD')
    contents = utils.read_file(self.MASTER_FILE)
    self.assertTrue('uncommitted' in contents)
    self.assertTrue('contents 2' in contents)

#  def test_uncommitted_untracked_changes_that_conflict(self):
#    utils.write_file(self.OTHER_FILE, contents='uncommitted in master')
#    try:
#      tbd.fuse(self.OTHER)
#      self.fail()
#    except ErrorReturnCode as e:
#      self.assertTrue('failed to apply' in utils.stderr(e))


class TestMerge(TestOp):

  def test_uncommitted_changes(self):
    utils.write_file(self.MASTER_FILE, contents='uncommitted')
    utils.write_file('master_untracked', contents='uncommitted')
    tbd.merge(self.OTHER)
    self.assertEqual('uncommitted', utils.read_file(self.MASTER_FILE))
    self.assertEqual('uncommitted', utils.read_file('master_untracked'))

  def test_uncommitted_tracked_changes_that_conflict(self):
    tbd.branch(c='tmp', divergent_point='HEAD~1')
    tbd.switch('tmp')
    utils.write_file(self.MASTER_FILE, contents='uncommitted')
    self.assertRaisesRegexp(
        ErrorReturnCode, 'failed to apply', tbd.merge, 'master')
    contents = utils.read_file(self.MASTER_FILE)
    self.assertTrue('uncommitted' in contents)
    self.assertTrue('contents 2' in contents)

  def test_uncommitted_tracked_changes_that_conflict_append(self):
    tbd.branch(c='tmp', divergent_point='HEAD~1')
    tbd.switch('tmp')
    utils.append_to_file(self.MASTER_FILE, contents='uncommitted')
    self.assertRaisesRegexp(
        ErrorReturnCode, 'failed to apply', tbd.merge, 'master')
    contents = utils.read_file(self.MASTER_FILE)
    self.assertTrue('uncommitted' in contents)
    self.assertTrue('contents 2' in contents)


class TestPerformance(TestEndToEnd):

  FPS_QTY = 10000

  def setUp(self):
    super(TestPerformance, self).setUp()
    for i in range(0, self.FPS_QTY):
      fp = 'f' + text(i)
      utils.write_file(fp, fp)

  def test_status_performance(self):
    def assert_status_performance():
      # The test fails if `tbd status` takes more than 100 times
      # the time `git status` took.
      MAX_TOLERANCE = 100

      t = time.time()
      tbd.status()
      tbd_t = time.time() - t

      t = time.time()
      git.status()
      git_t = time.time() - t

      self.assertTrue(
          tbd_t < git_t*MAX_TOLERANCE,
          msg='tbd_t {0}, git_t {1}'.format(tbd_t, git_t))

    # All files are untracked
    assert_status_performance()
    # Track all files, repeat
    logging.info('Doing a massive git add, this might take a while')
    git.add('.')
    logging.info('Done')
    assert_status_performance()

  def test_branch_switch_performance(self):
    MAX_TOLERANCE = 100

    tbd.commit('f1', m='commit')

    t = time.time()
    tbd.branch(c='develop')
    tbd.switch('develop')
    tbd_t = time.time() - t

    # go back to previous state
    tbd.switch('master')

    # do the same for git
    t = time.time()
    git.branch('gitdev')
    git.stash.save('--all')
    git.checkout('gitdev')
    git_t = time.time() - t

    self.assertTrue(
        tbd_t < git_t*MAX_TOLERANCE,
        msg='tbd_t {0}, git_t {1}'.format(tbd_t, git_t))
