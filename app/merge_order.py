import html
from itertools import product

import pandas as pd
from _templates import merge_preview_template
from order_file_io import _is_file_encrypted, decrypt_bytes
from order_settings import (
    PlatformHeaderVariableMap,
    find_matching_variable_map,
    load_order_variables_from_local_storage,
)
from pyscript import document, window


def translate_df(
    target_df: pd.DataFrame, variable_map: PlatformHeaderVariableMap
) -> pd.DataFrame:
    translated_df = pd.DataFrame()
    relevant_mappings = {
        key: value
        for key, value in variable_map.variable_mapping.items()
        if len(value) > 0
    }
    # Note that pd.concat is not suitable here
    # since it does not allow duplicating values.
    # some platforms might use one column for multiple unified variables.
    # or they can simply have the same values.
    # i.e. (reciepient_phone_number, buyer_phone_number) could be the smae.
    for unified_header, platform_header in relevant_mappings.items():
        translated_df[unified_header] = target_df[platform_header]
    return translated_df


def render_merge_preview() -> str:
    from order_file_io import _order_files

    variable_mapping = load_order_variables_from_local_storage()
    rows = []
    for file_name in _order_files:
        try:
            if _is_file_encrypted(file_name):
                file_bytes = decrypt_bytes(file_name)
            else:
                file_bytes = _order_files[file_name]
            variable_map = find_matching_variable_map(
                file_bytes, variable_mapping.platform_header_variable_maps
            )
            if variable_map is None:
                window.console.log("Could not find the matching platform.")
            else:
                original_df = pd.read_excel(
                    file_bytes, header=variable_map.header, dtype=str, nrows=1
                ).fillna("")
                translated = translate_df(original_df, variable_map)
                row = [file_name]
                for i_row, col in product(
                    range(len(translated)), variable_mapping.unified_header
                ):
                    if col not in translated.columns:
                        row.append('')
                    else:
                        cell = translated.at[i_row, col]
                        if (item_length := len(cell)) > 2:
                            hidden_part = '-' * (item_length - 2)
                            row.append(html.escape(cell[:2] + hidden_part))
                        else:
                            row.append(html.escape(cell))
                rows.append(row)
        except KeyError:  # noqa: PERF203
            # Skip the encrypted file with invalid password.
            ...

    return merge_preview_template.render(
        header_items=['통합변수', *variable_mapping.unified_header], rows=rows
    )


def refresh_merge_file_preview() -> None:
    preview = document.getElementById("order-render-preview-box")
    table = document.createElement("table")
    table.innerHTML = render_merge_preview()
    for child in preview.children:
        child.remove()
    preview.appendChild(table)
