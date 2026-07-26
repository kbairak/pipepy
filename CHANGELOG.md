# 0.0.12

Features:

- Migrated to uv build system (hatchling)
- Added mkdocs-based documentation
- Added type hints to main module

Misc:

- Updated .gitignore for uv/hatchling/mkdocs artifacts
- Added uv.lock
- Updated CI to use uv
- Updated PyPI metadata

# 0.0.9

Bugfixes:

- ([Github issue](https://github.com/kbairak/pipepy/issues/7)) When a binary
  (`_text=False`) command redirects from/to a file, `open` was being passed
  a binary mode (eg `rb`) and a not-`None` encoding. This raised an error.

Readme:

- Redirect from/to file example:

  ```python
  command < 'in' > 'out'    # Wrong!
  (command < 'in') > 'out'  # Correct!
  ```

Misc:

- Add changelog
