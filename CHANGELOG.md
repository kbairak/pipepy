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
