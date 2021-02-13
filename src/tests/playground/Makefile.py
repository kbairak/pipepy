DEFAULT_PYMAKE_TARGET = "echo1"


def echo1(msg1="world"):
    print(f"hello {msg1}")


msg2 = "world"


def echo2(msg2):
    print(f"hello {msg2}")


def echo3(echo1, echo2):
    pass


def echo4(echo3, echo1):
    pass
