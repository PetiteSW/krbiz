"""
# Reason why we use `xlsx` for configrutation files.

Even though `xlsx` files need extra handling to read and write,
we use `xlsx` files for configuration files for end-users.

Excel files are broadly used in Korean business platforms.
Therefore it is more familiar to end-users than other formats.

"""

import io
import pathlib

import msoffcrypto
import pandas as pd


def load_excel_file(
    file_path: str | pathlib.Path, header_row: int = 0, password: str | None = None
) -> pd.DataFrame:
    if password is None:
        return pd.read_excel(file_path, header=header_row)
    else:
        decrypted = io.BytesIO()

        with open(file_path, "rb") as f:
            file = msoffcrypto.OfficeFile(f)
            file.load_key(password=password)
            file.decrypt(decrypted)
            return pd.read_excel(decrypted, header=header_row)


def save_excel_file(
    df: pd.DataFrame,
    file_path: str | pathlib.Path,
) -> None:
    df.to_excel(file_path)


ORDER_DELIVERY_MAP_TEMPLATE_PATH = (
    pathlib.Path(__file__).parent / "_order_delivery_map_template.xlsx"
)
