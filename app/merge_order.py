import io
import json
import pathlib
from dataclasses import dataclass

import pandas as pd
from excel_helpers import export_excel
from js import URL, File, Uint8Array
from pyscript import document, window


@dataclass
class PlatformHeaderVariableMap:
    """Platform header variable mapping."""

    platform: str
    header: int
    variable_mapping: dict[str, str]


LATEST_ORDER_VARIABLE_CONFIG_FILE_PATH = pathlib.Path(
    "_resources/krbiz_order_unified_row_names.xlsx"
)
DEFAULT_ORDER_VARIABLE_CONFIG_FILE_PATH = pathlib.Path(
    "_resources/default_krbiz_order_unified_row_names.xlsx"
)

_ORDER_VARIABLE_SETTING_LOCAL_STORAGE_KEY = "ORDER-HEADER-VARIABLES"
"""DO NOT CHANGE this without supporting background compatibility."""


def _initialize_order_variables_in_local_storage() -> None:
    """Initialize local storage with order variables.

    This function should be called only when the web application
    is loaded for the first time.
    """
    window.console.log("Initializing order variables from the default file.")
    order_variables = pd.read_excel(DEFAULT_ORDER_VARIABLE_CONFIG_FILE_PATH, header=0)
    local_storage = window.localStorage
    if local_storage.getItem(_ORDER_VARIABLE_SETTING_LOCAL_STORAGE_KEY) is not None:
        window.console.log("Overwriting the existing order header variable settings.")
    order_variables_str = json.dumps(order_variables.to_dict(), ensure_ascii=False)
    local_storage.setItem(
        _ORDER_VARIABLE_SETTING_LOCAL_STORAGE_KEY, order_variables_str
    )


@dataclass
class VariableMappings:
    """Variable mapping to delivery information headers from different platforms."""

    platform_header_variable_maps: list[PlatformHeaderVariableMap]

    @property
    def unified_header(self) -> tuple[str, ...]:
        from functools import reduce

        key_set_list = [
            set(mapping.variable_mapping.keys())
            for mapping in self.platform_header_variable_maps
        ]
        return tuple(reduce(lambda x, y: x.union(y), key_set_list))

    @classmethod
    def from_dataframe(cls, mapping_df: pd.DataFrame) -> "VariableMappings":
        mapping_df = mapping_df.fillna("")

        return cls(
            platform_header_variable_maps=[
                PlatformHeaderVariableMap(
                    platform=row["Platform Name"],
                    header=row["Header Row"],
                    variable_mapping={col: row[col] for col in mapping_df.columns[2:]},
                )
                for _, row in mapping_df.iterrows()
            ]
        )


def load_order_variables_as_dataframe_from_local_storage() -> pd.DataFrame:
    local_storage = window.localStorage
    if local_storage.getItem(_ORDER_VARIABLE_SETTING_LOCAL_STORAGE_KEY) is None:
        _initialize_order_variables_in_local_storage()
    else:
        window.console.log("Found the existing order variable settings.")
    try:
        order_variables_dict = json.loads(
            local_storage.getItem(_ORDER_VARIABLE_SETTING_LOCAL_STORAGE_KEY)
        )
        return pd.DataFrame.from_dict(order_variables_dict)
    except Exception:
        window.console.log(
            "Error occurred while loading existing variable settings. "
            "Please reset the settings."
        )


def load_order_variables_from_local_storage() -> VariableMappings:
    df = load_order_variables_as_dataframe_from_local_storage()
    return VariableMappings.from_dataframe(df)


def _make_order_variable_preview_row(row_items: list[str]) -> str:
    return (
        '<tr class="table-header"><td class="index-column">'
        + "</td><td>".join(row_items)
        + "</td></tr>"
    )


def refresh_order_variable_preview() -> None:
    variable_mappings = load_order_variables_from_local_storage()
    unified_header = variable_mappings.unified_header
    header_row = _make_order_variable_preview_row(["통합변수", *unified_header])
    rows = [
        _make_order_variable_preview_row(
            [
                platform.platform,
                *(
                    platform.variable_mapping[unified_var]
                    for unified_var in unified_header
                ),
            ]
        )
        for platform in variable_mappings.platform_header_variable_maps
    ]
    preview_box = document.getElementById("order-variable-preview-box")
    table = document.createElement("table")
    # Clear the box
    for child in preview_box.children:
        child.remove()
    # Append the table
    table.innerHTML = f'<table>{"".join([header_row, *rows])}</table>'
    preview_box.appendChild(table)


def upload_new_order_variable_settings(e):
    window.console.log(e.currentTarget)


def download_current_order_variable_settings(e):
    window.console.log("Preparing the variable setting file.")
    df = load_order_variables_as_dataframe_from_local_storage()
    bytes = io.BytesIO()
    export_excel(df, bytes)
    bytes_buffer = bytes.getbuffer()
    js_array = Uint8Array.new(bytes_buffer.nbytes)
    js_array.assign(bytes_buffer)

    file = File.new(
        [js_array], LATEST_ORDER_VARIABLE_CONFIG_FILE_PATH.name, {type: "text/plain"}
    )
    url = URL.createObjectURL(file)

    hidden_link = document.createElement("a")
    hidden_link.setAttribute("download", LATEST_ORDER_VARIABLE_CONFIG_FILE_PATH.name)
    hidden_link.setAttribute("href", url)
    hidden_link.click()
    del hidden_link


def reset_order_variable_settings(_):
    _initialize_order_variables_in_local_storage()
    refresh_order_variable_preview()
