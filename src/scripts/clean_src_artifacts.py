#!/usr/bin/env python3
"""
Scan src/ for artifact files and remove untracked ones safely.
Does NOT follow symlinks.
"""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT
EXTS = {'.zip', '.srt', '.log', '.txt'}
DIR_NAMES = {'dist', 'build'}

def is_git_tracked(path: Path) -> bool:
    try:
        subprocess.check_output(['git', 'ls-files', '--error-unmatch', str(path)], cwd=ROOT, stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False

found_files = []
found_dirs = set()

for dirpath, dirnames, filenames in os.walk(SRC, followlinks=False):
    # avoid walking into .git
    if '.git' in dirpath.split(os.sep):
        continue
    # check dirs
    for d in list(dirnames):
        if d in DIR_NAMES:
            found_dirs.add(Path(dirpath) / d)
    for f in filenames:
        p = Path(dirpath) / f
        if p.suffix.lower() in EXTS:
            found_files.append(p)

print('Found candidate files:')
for p in found_files:
    print('  ', p)
print('\nFound candidate dirs:')
for d in sorted(found_dirs):
    print('  ', d)

# Delete files (skip tracked)
removed_files = []
skipped_files = []
for p in found_files:
    if is_git_tracked(p):
        skipped_files.append((p, 'tracked'))
        continue
    try:
        p.unlink()
        removed_files.append(p)
    except Exception as e:
        skipped_files.append((p, f'error:{e}'))

# Remove dirs if untracked and safe
removed_dirs = []
skipped_dirs = []
for d in sorted(found_dirs, key=lambda x: len(str(x)), reverse=True):
    # ensure dir exists
    if not d.exists():
        continue
    # check if any tracked files inside
    tracked_inside = False
    for root, dirs, files in os.walk(d, followlinks=False):
        for f in files:
            p = Path(root) / f
            if is_git_tracked(p):
                tracked_inside = True
                break
        if tracked_inside:
            break
    if tracked_inside:
        skipped_dirs.append((d, 'contains tracked files'))
        continue
    # safe to remove
    try:
        # remove recursively
        for root, dirs, files in os.walk(d, topdown=False, followlinks=False):
            for f in files:
                try:
                    (Path(root)/f).unlink()
                except Exception:
                    pass
            for dd in dirs:
                try:
                    (Path(root)/dd).rmdir()
                except Exception:
                    pass
        try:
            d.rmdir()
            removed_dirs.append(d)
        except Exception:
            # maybe not empty
            skipped_dirs.append((d, 'not empty or error'))
    except Exception as e:
        skipped_dirs.append((d, f'error:{e}'))

print('\nRemoved files:')
for p in removed_files:
    print('  ', p)
print('\nSkipped files:')
for p, reason in skipped_files:
    print('  ', p, reason)
print('\nRemoved dirs:')
for d in removed_dirs:
    print('  ', d)
print('\nSkipped dirs:')
for d, reason in skipped_dirs:
    print('  ', d, reason)

print('\nDone.')
