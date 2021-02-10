import os
import stat as stat_  # aliasing because there's a 'stat' UNIX command
import string

from .pipepy import PipePy


def overload_chars(locals_):
    """ Assigns all ascii characters as values to keys of the same name in the
        `locals_` argument. Intended to overload the `locals()` call of modules
        that import `pipepy`

            >>> from pipepy import overload_chars, ls
            >>> overload_chars(locals())
            >>> ls -l
            <<< -rw-r--r-- 1 kbairak kbairak 9401 Feb  3 23:12 foo.txt
            ... -rw-r--r-- 1 kbairak kbairak 8923 Feb  3 23:06 bar.txt
    """

    for char in string.ascii_letters:
        if char in locals_:
            continue
        locals_[char] = char


for path in os.get_exec_path():
    try:
        listdir = os.listdir(path)
    except FileNotFoundError:
        continue
    for original_name in listdir:
        name = original_name.replace('-', '_')
        if name in locals():
            continue
        if 'x' in stat_.filemode(
                os.lstat(os.path.join(path, original_name)).st_mode):
            locals()[name] = PipePy(original_name)

cd = os.chdir
export = os.environ.__setitem__
