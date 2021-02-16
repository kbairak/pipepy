import time

from pipepy import PipePy

echo_messages = PipePy('python', 'src/tests/playground/echo_messages.py')


def test_wait():
    tic = time.time()
    command = echo_messages(count=3, delay=.1, message='message {}').delay()
    command.wait()
    toc = time.time()
    assert .3 < toc - tic
    assert ([line.strip() for line in str(command).splitlines()] ==
            ["message 0", "message 1", "message 2"])


def test_terminate():
    command = echo_messages(count=10, delay=.1, message='message {}').delay()
    time.sleep(.23)  # Leave enough time for 2 messages
    command.terminate()
    command.wait()
    assert len([line.strip() for line in str(command).splitlines()]) < 10


def test_kill():
    command = echo_messages(count=10, delay=.1, message='message {}').delay()
    time.sleep(.23)  # Leave enough time for 2 messages
    command.kill()
    command.wait()
    assert len([line.strip() for line in str(command).splitlines()]) < 10
