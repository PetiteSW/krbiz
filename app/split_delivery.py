from _templates import delivery_split_row_template, delivery_split_table_template
from excel_helpers import load_excel
from js import window, document
from order_file_io import get_bytes_from_file, load_order_file
from order_settings import find_matching_variable_map, load_order_variables_from_local_storage

_delivery_confirmation = {}
_DELIVERY_SPLIT_RESULT_CONTAINER_ID = "delivery-split-result-container"
_DELIVERY_SPLIT_RESULT_TABLE_ID = "delivery-split-result-table"


def clear_delivery_result_container() -> None:
    container = document.getElementById(_DELIVERY_SPLIT_RESULT_CONTAINER_ID)
    for child in container.children:
        container.removeChild(child)


def get_valid_orders() -> dict:
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
        file_name: file_bytes
        for file_name, file_bytes in files.items()
        if find_matching_variable_map(file_bytes, variable_maps) is not None
    }


def refresh_delivery_split_result() -> None:
    orders = get_valid_orders()
    new_rows = [
        delivery_split_row_template.render(
            file_name=file_name
        )
        for file_name, file_bytes in orders.items()
    ]
    clear_delivery_result_container()
    table = document.createElement('table')
    table.id = _DELIVERY_SPLIT_RESULT_TABLE_ID
    table.innerHTML = delivery_split_table_template.render(file_items=new_rows)
    window.console.log(delivery_split_table_template.render(file_items=new_rows))
    container = document.getElementById(_DELIVERY_SPLIT_RESULT_CONTAINER_ID)
    container.appendChild(table)
    # Add event listener to the download button
    # for file_name in _order_files:
    #     button = document.getElementById(_make_button_id(file_name))
    #     when("click", button)(delete_file)


async def upload_delivery_confirmation(e):
    file_list = e.target.files
    new_file = next(iter(file_list))
    window.console.log("Delivery confirmation uploaded: " + new_file.name)
    new_delivery_confirmation = load_excel(await get_bytes_from_file(new_file))
    _delivery_confirmation.update({new_file.name: new_delivery_confirmation})
    window.console.log(str(new_delivery_confirmation))
    refresh_delivery_split_result()
