# Pipes

The `|` operator customizes where a command gets its input from and what it does with its output. Depending on the types of the operands, different behaviors emerge.

## Overview

| Left operand | Right operand | Behavior |
|---|---|---|
| `PipePy` | `PipePy` | Shell-like pipe: left stdout → right stdin |
| Iterable (incl. string) | `PipePy` | Elements fed to command's stdin |
| `PipePy` | Function | Process output with Python function |
| `PipePy` | Generator | Bidirectional streaming via yield/send |

For shell users, this is analogous to piping, but with Python objects anywhere in the chain.
