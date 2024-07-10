import argparse
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


def load_order_delivery_map() -> pd.DataFrame:
    if not ORDER_DELIVERY_MAP_FILE_PATH.exists():
        reset_order_delivery_map()

    return pd.read_excel(ORDER_DELIVERY_MAP_FILE_PATH)


def _build_default_download_dir() -> pathlib.Path:
    import datetime
    import time

    today = datetime.date.fromtimestamp(time.time())  # noqa: DTZ012
    today_directory = pathlib.Path(today.strftime("%Y-%m-%d-orders"))
    if (
        not (dir_path := pathlib.Path.home() / "Downloads").exists()
        and not (dir_path := pathlib.Path.home() / "다운로드").exists()
    ):
        working_dir = pathlib.Path.cwd()
    else:
        working_dir = dir_path

    return working_dir / today_directory


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    default_input_dir = _build_default_download_dir().as_posix()
    parser.add_argument(
        "--input-dir",
        dest="input_dir",
        help="Directory path that contains all the devliery excel files.\n"
        "Default is '{YY-mm-dd}-orders' in Downloads directory.\n"
        f"{default_input_dir}.",
        default=default_input_dir,
        type=str,
    )
    parser.add_argument(
        "--output", help="Output file path.", type=str, default="merged.xlsx"
    )
    return parser


def main():
    from .._logging import build_logger

    loggers = build_logger()
    parser = build_argparser()
    args = parser.parse_args()

    loggers.info(
        "Parsing order-delivery column mapping from ... %s",
        ORDER_DELIVERY_MAP_FILE_PATH,
    )
    loggers.info("Column mapping: \n%s", load_order_delivery_map())
    loggers.info("Looking for order files from: %s", args.input_dir)
    loggers.info("Merging orders to: %s", args.output)
