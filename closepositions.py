from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

positions = ib.positions()

for pos in positions:
    symbol = pos.contract.symbol
    currency = pos.contract.currency
    exchange = 'SMART'  # 👈 this is the fix
    contract = Stock(symbol, exchange, currency)

    quantity = pos.position
    action = 'SELL' if quantity > 0 else 'BUY'
    print(f"Closing {quantity} of {symbol} with {action} on SMART")

    order = MarketOrder(action, abs(quantity))
    ib.placeOrder(contract, order)

ib.sleep(5)
print("✅ All positions submitted for closing via SMART routing.")
ib.disconnect()


