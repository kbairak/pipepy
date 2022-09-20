import re
from typing import List


def strip_leading_spaces(text: str):
    text = text.splitlines()
    for line in text:
        if not line.strip():
            continue
        # First non-empty line
        indentation = len(re.search(r"^\s*", line).group())
        break
    else:
        raise ValueError("Text has no non-empty lines")

    result: List[str] = []
    for i, line in enumerate(text):
        left, right = line[:indentation], line[indentation:]
        if left.strip():
            raise ValueError(f"Line {i + 1} is not indented properly")
        result.append(right)
    return "\n".join(result)
