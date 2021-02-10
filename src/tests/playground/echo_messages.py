import argparse
import itertools
import sys
import time

parser = argparse.ArgumentParser(description="Print messages for testing")
parser.add_argument("-c", "--count", type=int, default=-1)
parser.add_argument("-d", "--delay", type=float, default=.1)
parser.add_argument("-m", "--message", default="")
parser.add_argument("-s", "--stream",
                    choices=['stdout', 'stderr'],
                    default="stdout")

if __name__ == "__main__":
    args = parser.parse_args()

    if args.count < 0:
        up = itertools.count()
    else:
        up = range(args.count)

    if args.stream == "stdout":
        stream = sys.stdout
    elif args.stream == "stderr":
        stream = sys.stderr

    for i in up:
        if args.message:
            try:
                message = args.message.format(i)
            except Exception:
                message = args.message
            stream.write(message + "\n")
        else:
            stream.write(i)
        stream.flush()
        time.sleep(args.delay)
