import argparse
import io
import logging
import pathlib
import shutil
from dataclasses import dataclass

import msoffcrypto
import pandas as pd
import xlrd

from .._resources import ORDER_DELIVERY_CONFIG_TEMPLATE_PATH
from ..configurations import DEFAULT_DIR

ORDER_DELIVERY_CONFIG_FILE_NAME = "order_delivery_config.xlsx"
ORDER_DELIVERY_CONFIG_FILE_PATH = DEFAULT_DIR / ORDER_DELIVERY_CONFIG_TEMPLATE_PATH


@dataclass
class PlatformHeaderVariableMap:
    """Platform header variable mapping."""

    platform: str
    header: int
    variable_mapping: dict[str, str]


@dataclass
class DeliveryInfoSchema:
    """Delivery information schema."""

    delivery_agency: str
    templates: pd.DataFrame

    @classmethod
    def from_excel(
        cls, file_path: str | pathlib.Path, sheet_name: str
    ) -> "DeliveryInfoSchema":
        return cls(
            delivery_agency=sheet_name,
            templates=pd.read_excel(file_path, sheet_name=sheet_name, header=0).fillna(
                ""
            ),
        )

    def order_info_to_delivery_info(self, order_info: pd.DataFrame) -> pd.DataFrame:
        new_row = self.templates.copy(deep=True)
        for col in self.templates.columns:
            rendered = self.templates[col].values[0]
            for order_col in order_info.columns:
                target = "{" + order_col + "}"
                rendered.replace(target, order_info[order_col].values[0])

            new_row.at[0, col] = rendered

        return new_row


@dataclass
class VariableMappings:
    """Variable mapping to delivery information headers from different platforms."""

    platform_header_variable_maps: list[PlatformHeaderVariableMap]
    delivery_info_headers: DeliveryInfoSchema

    @classmethod
    def from_excel(cls, file_path: str | pathlib.Path) -> "VariableMappings":
        mapping_df = pd.read_excel(
            file_path, sheet_name="variable_mapping", header=0
        ).fillna("")

        return cls(
            platform_header_variable_maps=[
                PlatformHeaderVariableMap(
                    platform=row["Name"],
                    header=row["Header Row"],
                    variable_mapping={col: row[col] for col in mapping_df.columns[2:]},
                )
                for _, row in mapping_df.iterrows()
            ],
            delivery_info_headers=DeliveryInfoSchema.from_excel(
                file_path, str(pd.ExcelFile(file_path).sheet_names[1])
            ),
        )


def reset_order_delivery_map() -> None:
    shutil.copy(ORDER_DELIVERY_CONFIG_TEMPLATE_PATH, ORDER_DELIVERY_CONFIG_FILE_PATH)


def get_order_delivery_config_path() -> pathlib.Path:
    if not ORDER_DELIVERY_CONFIG_FILE_PATH.exists():
        reset_order_delivery_map()

    return ORDER_DELIVERY_CONFIG_FILE_PATH


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


def match_column_names(df: pd.DataFrame, mappings: dict[str, str]) -> bool:
    for platform_name in mappings.values():
        if platform_name and platform_name not in df.columns:
            return False
    return True


def _reverse_mapping(mapping: dict[str, str]) -> dict[str, str]:
    return {v: k for k, v in mapping.items()}


def _collect_relevant_columns(
    df: pd.DataFrame, mappings: PlatformHeaderVariableMap
) -> pd.DataFrame:
    columns = [df[target] for target in mappings.variable_mapping.values() if target]
    relevants = pd.concat(columns, axis=1)
    return relevants.rename(
        _reverse_mapping(mappings.variable_mapping),
        axis=1,
    )


def file_to_dataframe(
    file_path: str | pathlib.Path,
    mappings: list[PlatformHeaderVariableMap],
    logger: logging.Logger,
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
    for mapping in mappings:
        df = load_excel_file(file_path, mapping.header - 1, password)
        if not match_column_names(df, mapping.variable_mapping):
            continue
        logger.info("Matched platform: %s", mapping.platform)
        return _collect_relevant_columns(df, mapping)

    return None


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
    order_files = collect_files(args.input_dir)
    order_file_names = [file.name for file in order_files]
    logger.info("Found %d order files. %s", len(order_files), order_file_names)

    merged_df = None
    logger.info("Processing orders %s...", order_files)
    for order_file in order_files:
        logger.info("Loading %s ...", order_file)
        df = file_to_dataframe(
            order_file, variable_mappings.platform_header_variable_maps, logger
        )
        if df is None:
            logger.error(
                "Failed to load %s. Please check the column names.", order_file
            )
            continue

        logger.info("%s orders found in %s : ", len(df), order_file)
        if merged_df is None:
            merged_df = df
        else:
            merged_df = pd.concat([merged_df, df], ignore_index=True)

    logger.info("Total orders: %s", merged_df)
    logger.info("Merging orders to: %s ...", args.output)
