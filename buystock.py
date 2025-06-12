from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)  # paper account port

stocks = ['NET']

for symbol in stocks:
    contract = Stock(symbol, 'SMART', 'USD')
    ib.qualifyContracts(contract)
    order = MarketOrder('Buy', 100)
    trade = ib.placeOrder(contract, order)
    print(f"Placed order for {symbol}")
    ib.sleep(1)  # short pause to avoid pacing violations

# Account summary details
account_summary = ib.accountSummary()

for item in account_summary:
    if item.tag == 'AvailableFunds':
        print(f"Available Funds: {item.value} {item.currency}")
    elif item.tag == 'BuyingPower':
        print(f"Buying Power: {item.value} {item.currency}")

ib.disconnect()
