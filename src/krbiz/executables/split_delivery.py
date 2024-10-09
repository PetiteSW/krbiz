import pathlib
from dataclasses import dataclass

import pandas as pd
import xlrd

from .merge_orders import (
    ORDER_DELIVERY_CONFIG_FILE_PATH,
    VariableMappings,
    build_argparser,
    collect_files,
    file_to_raw_dataframe,
    get_order_delivery_config_path,
)

_columns_for_matching = ("수하인명", "수하인기본주소", "상품명", "내품개수")
_columns_for_finding_delivery_file = _columns_for_matching


def _match_header(file_path: pathlib.Path) -> bool:
    try:
        header_df = pd.read_excel(
            file_path,
            sheet_name=str(pd.ExcelFile(file_path).sheet_names[0]),
            header=0,
            nrows=0,
        )
        return all(
            column_name in header_df.columns
            for column_name in _columns_for_finding_delivery_file
        )
    except xlrd.biffh.XLRDError:
        return False  # Assuming delivery file is not encrypted.


class MultipleDeliveryFilesFound(Exception): ...


def find_delivery_file(file_paths: list[pathlib.Path]) -> pathlib.Path:
    matched = [file_path for file_path in file_paths if _match_header(file_path)]
    if len(matched) > 1:  # Should find exactly one delivery file.
        raise MultipleDeliveryFilesFound(
            "Multiple files found: ", matched, "\nShould only have one delivery file."
        )  # TODO: Better error messages.
    return next(iter(matched))


def load_delivery_file(file_path: pathlib.Path) -> pd.DataFrame:
    return pd.read_excel(
        file_path, sheet_name=str(pd.ExcelFile(file_path).sheet_names[0]), header=0
    ).fillna("")


def load_original_files() -> VariableMappings: ...


def validate_delivery_file_and_original_files(
    original_files: dict[str, pd.DataFrame], delivery_file: pd.DataFrame
):
    if sum(len(df) for df in original_files.values()) != len(delivery_file):
        raise ValueError("Number of original orders and delivery cases do not match.")


@dataclass
class DeliveryToOrder:
    platform: str
    original_df: pd.DataFrame
    delivery_df: pd.DataFrame


def split_delivery_information() -> dict[str, DeliveryToOrder]: ...


def main():
    from .._logging import build_logger

    logger = build_logger()
    parser = build_argparser()
    args = parser.parse_args()

    logger.info(
        "Parsing order-delivery column mapping from ... %s",
        ORDER_DELIVERY_CONFIG_FILE_PATH,
    )
    variable_mappings = VariableMappings.from_excel(get_order_delivery_config_path())
    logger.info("Processing files using variable mappings: \n%s", variable_mappings)

    logger.info("Collecting order files from: %s ...", args.input_dir)
    if args.all:
        order_files = collect_files(args.input_dir, only_today=False)
    else:
        order_files = collect_files(args.input_dir, only_today=True)

    order_file_names = [file.name for file in order_files]
    logger.info("Found %d order files. %s", len(order_files), order_file_names)

    delivery_file_path = find_delivery_file(order_files)
    logger.info("Delivery information found: %s", delivery_file_path)
    delivery_file = load_delivery_file(delivery_file_path)

    logger.info("Start splitting per platform ...")
    original_files: dict[str, pd.DataFrame] = {}
    for order_file_path in order_files:
        results = file_to_raw_dataframe(
            order_file_path,
            mappings=variable_mappings.platform_header_variable_maps,
            logger=logger,
        )
        if results is not None:
            mapping, df = results
            original_files[mapping.platform] = df
            logger.info("Found a file matched with platform, %s.", mapping.platform)

    validate_delivery_file_and_original_files(original_files, delivery_file)
