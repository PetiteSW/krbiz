import io
import pathlib

import pandas as pd


def _adjust_column_width(sheet, ref_df: pd.DataFrame) -> None:
    for i_col, col in enumerate(ref_df.columns):
        max_length = max(
            int(ref_df[col].astype(str).map(len).max()),
            len(col),
        )
        sheet.set_column(i_col, i_col, min(max_length * 2 + 1, 50))


def export_excel(
    df: pd.DataFrame, output_file_path: pathlib.Path | io.BytesIO, pretty: bool = True
) -> None:
    with pd.ExcelWriter(output_file_path, engine="xlsxwriter") as writer:
        df.to_excel(excel_writer=writer, index=False)
        if pretty:
            for sheet in writer.sheets.values():
                _adjust_column_width(sheet, df)
