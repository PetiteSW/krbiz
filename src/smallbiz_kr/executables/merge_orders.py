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


def _replace_single_variable(text: str, variable: str, value: str) -> str:
    return text.replace("{" + variable + "}", value)


def _render_variable(text: str, variable_mapping: dict[str, str]) -> str:
    for variable, value in variable_mapping.items():
        text = _replace_single_variable(text, variable, value)
    return text


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
        new_df = pd.concat(
            [self.templates.copy(deep=True)] * len(order_info), ignore_index=True
        )
        for i_new_df_row in range(len(new_df)):
            variable_mapping = {
                col: str(order_info.at[i_new_df_row, col]) for col in order_info.columns
            }
            for new_df_col in new_df.columns:
                new_df.at[i_new_df_row, new_df_col] = _render_variable(
                    new_df.at[i_new_df_row, new_df_col],
                    variable_mapping,
                )

        return new_df


@dataclass
class VariableMappings:
    """Variable mapping to delivery information headers from different platforms."""

    platform_header_variable_maps: list[PlatformHeaderVariableMap]
    delivery_info_headers: DeliveryInfoSchema

    @property
    def platform_header_variables(self) -> tuple[str, ...]:
        from functools import reduce

        key_set_list = [
            set(mapping.variable_mapping.keys())
            for mapping in self.platform_header_variable_maps
        ]
        return tuple(reduce(lambda x, y: x.union(y), key_set_list))

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
    logger.info("Loading %s ...", file_path)

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

    logger.error("Failed to load %s. Please check the column names.", file_path)
    return None


def merge_orders(
    order_files: list[pathlib.Path],
    variable_mappings: VariableMappings,
    logger: logging.Logger,
) -> pd.DataFrame:
    order_dfs = [
        df
        for order_file in order_files
        if (
            df := file_to_dataframe(
                order_file, variable_mappings.platform_header_variable_maps, logger
            )
        )
        is not None
    ]
    return pd.concat(order_dfs, ignore_index=True)


def _adjust_column_width(sheet, ref_df: pd.DataFrame) -> None:
    for i_col, col in enumerate(ref_df.columns):
        max_length = max(
            int(ref_df[col].astype(str).map(len).max()),
            len(col),
        )
        sheet.set_column(i_col, i_col, min(max_length*2 + 1, 50))


def export_excel(
    df: pd.DataFrame, output_file_path: pathlib.Path, pretty: bool = True
) -> None:
    with pd.ExcelWriter(output_file_path, engine="xlsxwriter") as writer:
        df.to_excel(excel_writer=writer, index=False)
        if pretty:
            for sheet in writer.sheets.values():
                # sheet.autofit()
                _adjust_column_width(sheet, df)


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

    logger.info("Processing orders %s...", order_files)
    merged_df = merge_orders(order_files, variable_mappings, logger)

    logger.debug("Merged orders: %s", merged_df)
    rendered_orders = (
        variable_mappings.delivery_info_headers.order_info_to_delivery_info(merged_df)
    )

    logger.debug("Total orders: %s", rendered_orders)
    logger.info("Exporting delivery information to: %s ...", args.output)
    export_excel(rendered_orders, args.output)
    logger.info("Exporting done. Check the file: %s", args.output)
