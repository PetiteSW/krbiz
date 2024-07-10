import pathlib
import shutil

import pandas as pd

from .._resources import (
    ORDER_DELIVERY_MAP_TEMPLATE_PATH as DEFAULT_ORDER_DELIVERY_MAP_TEMPLATE_PATH,
)
from ..configurations import DEFAULT_DIR

ORDER_DELIVERY_MAP_FILE_NAME = "order_delivery_map.xlsx"
ORDER_DELIVERY_MAP_FILE_PATH = DEFAULT_DIR / ORDER_DELIVERY_MAP_FILE_NAME


def reset_order_delivery_map() -> None:
    shutil.copy(DEFAULT_ORDER_DELIVERY_MAP_TEMPLATE_PATH, ORDER_DELIVERY_MAP_FILE_PATH)


def load_order_delivery_map(custom_path: pathlib.Path | None = None) -> pd.DataFrame:
    if custom_path is not None:
        if not custom_path.exists():
            raise FileNotFoundError(f"File not found: {custom_path}")

        return pd.read_excel(custom_path)

    elif not ORDER_DELIVERY_MAP_FILE_PATH.exists():
        reset_order_delivery_map()

    return pd.read_excel(ORDER_DELIVERY_MAP_FILE_PATH)


def main():
    from .._logging import build_logger
    loggers = build_logger()
    loggers.info(load_order_delivery_map())
