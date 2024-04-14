"""
Unimportant Helper functions - Possibly remove
"""

import io
import logging

from matplotlib import pyplot as plt
from .extendend_bars import ExtendedBar, ExtendedBarSet


def get_times_and_closing_p(data: list[ExtendedBar]) -> tuple[list, list]:
    """
    return useful data from barset
    """
    times, closing_prices = [], []
    for point in data:
        times.append(point.timestamp)
        closing_prices.append(point.close)
    return times, closing_prices


def plot_stock_data(data: ExtendedBarSet):
    """
    Plot the historical stock data using matplotlib.

    data: List of dictionaries,where each dictionary contains
    the 'time' and 'close' price of a data point.
    """
    image_buffs = []
    for key in data.data.keys():
        logging.info("Plotting data for %s..", key)
        times, closing_prices = get_times_and_closing_p(data.data[key])
        plt.figure(figsize=(10, 6))
        plt.plot(times, closing_prices, marker="o", linestyle="-", color="b")
        plt.xlabel("Date")
        plt.ylabel("Closing Price")
        plt.title("Historical Stock Data")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format="png")
        image_buffs.append(img_buf.getvalue())
    return image_buffs
