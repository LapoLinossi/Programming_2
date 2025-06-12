# test_ibapi.py
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

print("EClient:", EClient)
print("EWrapper:", EWrapper)

class TestWrapper(EWrapper):
    pass

class TestClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

print("Import successful!")