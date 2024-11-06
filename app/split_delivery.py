import io
from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd
from _templates import (
    delivery_left_over_table_template,
    delivery_split_row_template,
    delivery_split_table_template,
)
from excel_helpers import export_excel, load_excel
from js import URL, File, Uint8Array
from order_file_io import get_bytes_from_file, load_order_file
from order_settings import (
    PlatformHeaderVariableMap,
    find_matching_variable_map,
    load_order_variables_from_local_storage,
)
from pyscript import document, when, window

_delivery_confirmation = {}

_DELIVERY_SPLIT_RESULT_CONTAINER_ID = "delivery-split-result-container"
_DELIVERY_SPLIT_RESULT_TABLE_ID = "delivery-split-result-table"


class DeliveryConfirmationFileSpec:
    _data_frame: pd.DataFrame
    _file_name: str

    @property
    def data_frame(self) -> pd.DataFrame:
        return self._data_frame

    @property
    def file_name(self) -> str:
        return self._file_name

    def __init__(self, file_name: str, df: pd.DataFrame) -> None:
        self._data_frame = df
        self._file_name = file_name


@dataclass
class ValidOrderFileSpec:
    file_name: str
    data_frame: pd.DataFrame
    variable_mapping: PlatformHeaderVariableMap


@dataclass
class DeliveryInforUpdatedFileSpec:
    file_name: str
    platform: str
    data_frame: pd.DataFrame


def clear_delivery_result_container() -> None:
    container = document.getElementById(_DELIVERY_SPLIT_RESULT_CONTAINER_ID)
    window.console.log(f"Removing {len(container.children)} children")
    container.replaceChildren()


def collect_valid_orders() -> dict[str, ValidOrderFileSpec]:
    from order_file_io import _order_files

    variable_mappings = load_order_variables_from_local_storage()
    variable_maps = variable_mappings.platform_header_variable_maps
    # Filter encrypted files
    files = {}
    for file_name in _order_files:
        try:
            file_bytes = load_order_file(file_name)
            files[file_name] = file_bytes
        except KeyError:  # noqa: PERF203
            ...  # Skip the invalid password file.

    return {
        file_name: ValidOrderFileSpec(
            file_name=file_name,
            data_frame=load_excel(file_bytes, var_map.header),
            variable_mapping=var_map,
        )
        for file_name, file_bytes in files.items()
        if (var_map := find_matching_variable_map(file_bytes, variable_maps))
        is not None
    }


def _get_download_button_id(file_name: str) -> str:
    return f"{file_name}-delivery-split-result-download-button"


def _render_delivery_download_button(file_spec: ValidOrderFileSpec) -> str:
    button_id = _get_download_button_id(file_spec.file_name)
    return f'<button class="small-button" id="{button_id}">💾</button>'


def _make_split_file_name(file_spec: DeliveryInforUpdatedFileSpec) -> str:
    today_as_str = pd.Timestamp.now().strftime("%Y-%m-%d")
    return f"{file_spec.platform}-delivered-{today_as_str}.xlsx"


def _generate_download_event_handler(
    file_spec: DeliveryInforUpdatedFileSpec,
) -> Callable:
    def download_delivery_split(_):
        window.console.log("Downloading split files.")
        # Download the split file.
        bytes = io.BytesIO()
        export_excel(file_spec.data_frame, bytes)
        bytes_buffer = bytes.getbuffer()
        js_array = Uint8Array.new(bytes_buffer.nbytes)
        js_array.assign(bytes_buffer)

        file_name = _make_split_file_name(file_spec)
        file = File.new([js_array], file_name, {type: "text/plain"})
        url = URL.createObjectURL(file)

        hidden_link = document.createElement("a")
        hidden_link.setAttribute("download", file_name)
        hidden_link.setAttribute("href", url)
        hidden_link.click()
        # Release the object URL and clean up.
        URL.revokeObjectURL(url)
        hidden_link.remove()
        del hidden_link

    return download_delivery_split


def _remove_empty_space(msgs: list[str]) -> list[str]:
    return [msg.strip() if isinstance(msg, str) else msg for msg in msgs]


def _are_matching_rows(delivery_row: pd.Series, order_row: pd.Series) -> bool:
    name_column = "수하인명"
    product_name_column = "상품명"
    delivery_note_column = "특기사항"
    must_match_cols = (
        name_column,
        product_name_column,
        delivery_note_column,
    )
    window.console.log(delivery_row['특기사항'])
    window.console.log(order_row.values)
    return all(
        (delivery_row[col] == '')
        or (delivery_row[col] in order_row.values)
        or (
            isinstance(delivery_row[col], str)
            and (delivery_row[col].strip() in _remove_empty_space(order_row.values))
        )
        for col in must_match_cols
    )


def _find_tracking_code_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        if '송장번호' in col:
            return col
    return '송장번호'


def insert_delivery_tracking_code(
    orders: dict[str, ValidOrderFileSpec],
    delivery_confirmation: DeliveryConfirmationFileSpec,
) -> tuple[dict[str, DeliveryInforUpdatedFileSpec], pd.DataFrame]:
    results = {
        file_name: [pd.DataFrame(columns=file_spec.data_frame.columns)]
        for file_name, file_spec in orders.items()
    }
    delivery_df = delivery_confirmation.data_frame.copy(deep=True)
    non_matched = []
    duplicated = []
    matches = {i_delivery_row: {} for i_delivery_row, _ in delivery_df.iterrows()}
    for i_delivery_row, delivery_row in delivery_df.iterrows():
        for file_name, order_file_spec in orders.items():
            for _, order_row in order_file_spec.data_frame.iterrows():
                if _are_matching_rows(delivery_row, order_row):
                    matches[i_delivery_row].setdefault(file_name, []).append(order_row)

    for i_delivery_row, delivery_row in delivery_df.iterrows():
        matched_files = matches[i_delivery_row]
        if not matched_files:
            non_matched.append(delivery_row)
        elif len(matched_files) > 2:
            duplicated.append(delivery_row)
        else:
            matched_file_name = next(iter(matched_files))
            matched_rows = matched_files[matched_file_name]
            if len(matched_rows) > 1:
                duplicated.append(delivery_row)
            else:
                matched_row = matched_rows[0]
                inserted = matched_row.to_frame().T
                tracking_code_col = _find_tracking_code_column(inserted)
                inserted[tracking_code_col] = delivery_row["운송장번호"]
                results[matched_file_name].append(inserted)

    merged_result = {file_name: pd.concat(rows) for file_name, rows in results.items()}
    left_over = pd.DataFrame(columns=delivery_confirmation.data_frame.columns)
    if duplicated:
        duplicated_dfs = [row.to_frame().T for row in duplicated]
        merged_duplications = pd.concat(duplicated_dfs)
        window.alert(
            f"총 {len(duplicated)}개의 운송장 정보를 입력할 수 없었습니다: \n"
            + ','.join(merged_duplications['운송장번호'])
        )
        left_over = pd.concat([left_over, merged_duplications])

    if non_matched:
        non_matched_dfs = [row.to_frame().T for row in non_matched]
        non_matched_duplications = pd.concat(non_matched_dfs)
        window.alert(
            f"총 {len(non_matched)}개의 운송장 정보를 입력할 수 없었습니다: \n"
            + ','.join(non_matched_duplications['운송장번호'])
        )
        left_over = pd.concat([left_over, non_matched_duplications])

    return {
        order_file_spec.file_name: DeliveryInforUpdatedFileSpec(
            file_name=order_file_spec.file_name,
            platform=order_file_spec.variable_mapping.platform,
            data_frame=merged_result[file_name],
        )
        for file_name, order_file_spec in orders.items()
    }, left_over.loc[:, (left_over != '').any()]


def render_leftover_delivery_info(container, left_over_df: pd.DataFrame) -> None:
    table = document.createElement('div')
    table.innerHTML = delivery_left_over_table_template.render(
        headers=left_over_df.columns,
        rows=[
            [row[col] for col in left_over_df.columns]
            for _, row in left_over_df.iterrows()
        ],
    )
    container.appendChild(table)


def refresh_delivery_split_result() -> None:
    if not _delivery_confirmation:
        window.alert("배송내역 파일을 먼저 올려주세요.")
        return

    orders = collect_valid_orders()
    new_rows = [
        delivery_split_row_template.render(
            file_name=file_name,
            platform_name=file_spec.variable_mapping.platform,
            download_button=_render_delivery_download_button(file_spec),
        )
        for file_name, file_spec in orders.items()
    ]
    clear_delivery_result_container()
    table = document.createElement('table')
    table.id = _DELIVERY_SPLIT_RESULT_TABLE_ID
    table.innerHTML = delivery_split_table_template.render(file_items=new_rows)
    container = document.getElementById(_DELIVERY_SPLIT_RESULT_CONTAINER_ID)
    container.appendChild(table)

    updated, left_over_df = insert_delivery_tracking_code(
        orders=orders, delivery_confirmation=_delivery_confirmation["latest"]
    )
    # Add event listener to the download button
    for file_name, file_spec in updated.items():
        button = document.getElementById(_get_download_button_id(file_name))
        when("click", button)(_generate_download_event_handler(file_spec))

    # Render left over ones if needed
    render_leftover_delivery_info(container, left_over_df)


async def save_delivery_confirmation_file(file_obj) -> None:
    new_delivery_confirmation = load_excel(await get_bytes_from_file(file_obj))
    _delivery_confirmation.update(
        {
            "latest": DeliveryConfirmationFileSpec(
                file_name=file_obj.name, df=new_delivery_confirmation
            )
        }
    )
    file_name_display = document.getElementById("delivery_confirmation_file_name")
    file_name_display.textContent = f"최근 업로드 된 파일: {file_obj.name}"


async def upload_delivery_confirmation(e):
    file_list = e.target.files
    try:
        new_file = next(iter(file_list))
    except StopIteration:
        window.console.log("No file selected.")
        return
    else:
        window.console.log("Delivery confirmation uploaded: " + new_file.name)

    try:
        await save_delivery_confirmation_file(new_file)
    except Exception as e:
        window.alert("배송 파일 업로드에 실패했습니다.")
    else:
        refresh_delivery_split_result()
