from datetime import datetime
import io
import json
import requests
from matplotlib import pyplot as plt


resp = requests.get(
    "http://localhost:8000/backtest/result/stats", params={"backtest_id": 122}
)
vals = resp.json()
balances = []
datetimes = []
for val in vals:
    poss = val["positions"].values()
    balance = val["balance"] + sum([float(pos["cost_basis"]) for pos in poss])

    balances.append(balance)
    datetimes.append(val["timestamp"])


def plot(values: list[float], timeseries: list[datetime]):
    """
    Plot the historical stock data using matplotlib.

    data: List of dictionaries,where each dictionary contains
    the 'time' and 'close' price of a data point.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(timeseries, values, marker="o", linestyle="-", color="b")
    plt.xlabel("Datetime")
    plt.ylabel("Balance")
    plt.title("Balance Plot")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("balance.png")


plot(balances, datetimes)
