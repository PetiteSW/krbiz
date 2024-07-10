import argparse
import io
import logging
import pathlib
import shutil

import msoffcrypto
import pandas as pd
import xlrd

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

    return pd.read_excel(ORDER_DELIVERY_MAP_FILE_PATH, header=0).fillna("")


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


def collect_files(input_dir: str | pathlib.Path) -> list[pathlib.Path]:
    dir_path = pathlib.Path(input_dir)
    cands = [*dir_path.glob("*.xlsx"), *dir_path.glob("*.xls")]
    return [file for file in cands if not file.name.startswith("~")]


def load_excel_file(
    file_path: str | pathlib.Path, header_row: int = 0, password: str | None = None
) -> pd.DataFrame:
    if password is None:
        return pd.read_excel(file_path, header=header_row).fillna("")
    else:
        decrypted = io.BytesIO()

        with open(file_path, "rb") as f:
            file = msoffcrypto.OfficeFile(f)
            file.load_key(password=password)
            file.decrypt(decrypted)
            return pd.read_excel(decrypted, header=header_row).fillna("")


def match_column_names(df: pd.DataFrame, mappings: pd.DataFrame) -> bool:
    for mapping_name in mappings.columns[2:]:  # From here
        if (cand := mappings[mapping_name].values[0]) and (cand not in df.columns):
            return False
    return True


def _collect_relevant_columns(df: pd.DataFrame, mappings: pd.DataFrame) -> pd.DataFrame:
    columns = [
        df[target]
        for mapping_name in mappings.columns[2:]
        if (target := mappings[mapping_name].values[0])
    ]
    relevants = pd.concat(columns, axis=1)
    return relevants.rename(
        {mappings[col].values[0]: col for col in mappings.columns[2:]}, axis=1
    )


def file_to_dataframe(
    file_path: str | pathlib.Path, mappings: pd.DataFrame, logger: logging.Logger
) -> pd.DataFrame | None:
    try:
        pd.read_excel(file_path)
    except xlrd.biffh.XLRDError:
        import rich

        password = rich.console.Console().input(
            f"\n[PASSWORD REQUIRED]\n{file_path} seems to be "
            "encrypted with password. Please enter the password: ",
            password=True,
        )
    else:
        password = None

    # Iterate throw rows
    for i_row in range(len(mappings)):
        cur_mapping_df = mappings.iloc[[i_row]]
        header_row = cur_mapping_df["Header Row"].values[0]
        df = load_excel_file(file_path, header_row - 1, password)
        if not match_column_names(df, cur_mapping_df):
            continue
        logger.info("Matched platform: %s", cur_mapping_df["Name"].values[0])
        return _collect_relevant_columns(df, cur_mapping_df)

    return None


def main():
    from .._logging import build_logger

    logger = build_logger()
    parser = build_argparser()
    args = parser.parse_args()

    logger.info(
        "Parsing order-delivery column mapping from ... %s",
        ORDER_DELIVERY_MAP_FILE_PATH,
    )
    logger.info("Column mapping: \n%s", (mappings := load_order_delivery_map()))
    logger.info("Collecting order files from: %s ...", args.input_dir)
    order_files = collect_files(args.input_dir)
    logger.info("Found %d order files.", len(order_files))
    logger.info("%s", [file.name for file in order_files])
    logger.info("Processing orders %s...", order_files)
    merged_df = None
    for order_file in order_files:
        logger.info("Loading %s ...", order_file)
        if (df := file_to_dataframe(order_file, mappings, logger)) is None:
            logger.error(
                "Failed to load %s. Please check the column names.", order_file
            )
            continue
        logger.info("Total orders: %s", df.columns)
        if merged_df is None:
            merged_df = df
        else:
            merged_df = pd.concat([merged_df, df], ignore_index=True)

        logger.info("Total orders: %s", merged_df)

    logger.info("Merging orders to: %s ...", args.output)
