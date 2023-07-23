import io
import logging

import numpy as np
from alpaca.data.models import BarSet
from matplotlib import pyplot as plt


def plot_stock_data(data: BarSet):
    """
    Plot the historical stock data using matplotlib.

    data: List of dictionaries,where each dictionary contains
    the 'time' and 'close' price of a data point.
    """
    image_buffs = []
    for key in data.data.keys():
        logging.info("Plotting data for %s..", key)
        closing_prices = []
        times = []
        data_points = data.data[key]
        for point in data_points:
            times.append(point.timestamp)
            closing_prices.append(point.close)
        np_closing = np.array(closing_prices, dtype=np.float64)
        moving_average = np.mean(np_closing)
        logging.info(moving_average)
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
