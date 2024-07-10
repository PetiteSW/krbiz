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
