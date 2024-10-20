import pathlib

import pandas as pd
from pyscript import window

LATEST_ORDER_VARIABLE_CONFIG_FILE_PATH = pathlib.Path(
    "_resources/krbiz_order_row_name_variables.xlsx"
)
DEFAULT_ORDER_VARIABLE_CONFIG_FILE_PATH = pathlib.Path(
    "_resources/default_krbiz_order_row_name_variables.xlsx"
)


def _initialize_order_variables_in_local_storage() -> None:
    """Initialize local storage with order variables.

    This function should be called only when the web application
    is loaded for the first time.
    """
    window.console.log("Initializing order variables from the default file.")
    order_variables = pd.read_excel(DEFAULT_ORDER_VARIABLE_CONFIG_FILE_PATH, header=0)
    window.console.log(order_variables.to_string())


def load_order_variables_from_local_storage() -> pd.DataFrame:
    local_storage = window.localStorage
    if local_storage.getItem("?") is None:
        _initialize_order_variables_in_local_storage()


def upload_new_order_variable_settings(e):
    window.console.log(e.currentTarget)


def download_current_order_variable_settings(e):
    window.console.log(e.currentTarget)


def reset_order_variable_settings(e):
    window.console.log(e.currentTarget)
