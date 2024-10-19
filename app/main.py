import io

from _templates import file_item_row_template, file_list_table_template
from pyscript import document, window
from pyscript.ffi import create_proxy

_order_files = {}  # Dictionary that carries uploaded files.


def clear_order_table_container() -> None:
    container = document.getElementById("order-file-list-table-container")
    for child in container.children:
        container.removeChild(child)


def initialize_order_list_table():
    clear_order_table_container()
    table = document.createElement('table')
    table.id = "order-file-list-table"
    table.innerHTML = file_list_table_template.render(
        file_items=[
            file_item_row_template.render()  # Empty row
        ]
    )
    container = document.getElementById("order-file-list-table-container")
    container.appendChild(table)


async def get_bytes_from_file(file):
    array_buf = await file.arrayBuffer()
    return io.BytesIO(array_buf.to_bytes())


def _make_row_id(file_name: str) -> str:
    return f"order-{file_name}-row"


def _make_button_id(file_name: str) -> str:
    return f"order-{file_name}-delete-button"


def _make_delete_button(file_name: str) -> str:
    button_id = _make_button_id(file_name)
    button_tag = (
        '<button type="button" class="delete-button" '
        + f'id="{button_id}" value="{file_name}">'
    )
    trash_icon = '<img src="trash_icon.png" alt="🗑️" height=1em>'
    return f'{button_tag}{trash_icon}</button>'


def delete_file(e) -> None:
    _file_name = e.currentTarget.value
    window.console.log(f"Deleting the order file: {_file_name}")
    row = document.getElementById(_make_row_id(_file_name))
    row.remove()
    _order_files.pop(_file_name, None)
    left_files = '\n'.join(_order_files.keys())
    window.console.log(f"Left order files: \n{left_files}")


def refresh_table_from_order_files() -> None:
    new_rows = [
        file_item_row_template.render(
            file_name=file_name, delete_button=_make_delete_button(file_name)
        )
        for file_name in _order_files
    ]
    clear_order_table_container()
    table = document.createElement('table')
    table.id = "order-file-list-table"
    table.innerHTML = file_list_table_template.render(file_items=new_rows)
    container = document.getElementById("order-file-list-table-container")
    container.appendChild(table)
    # Add event listener to the delete button
    for file_name in _order_files:
        button = document.getElementById(_make_button_id(file_name))
        button.addEventListener("click", create_proxy(delete_file))


async def upload_order_file(e):
    file_list = e.target.files
    names = [f.name for f in file_list]
    window.console.log("Files uploaded: " + ','.join(names))
    _order_files.update({f.name: await get_bytes_from_file(f) for f in file_list})
    refresh_table_from_order_files()


if __name__ == "__main__":
    # Initialize Order list table.
    initialize_order_list_table()
    document.getElementById("order-file-upload").addEventListener(
        "change", create_proxy(upload_order_file)
    )
