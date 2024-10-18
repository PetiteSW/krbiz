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


def refresh_table_from_order_files() -> None:
    new_rows = [
        file_item_row_template.render(file_name=file_name) for file_name in _order_files
    ]
    clear_order_table_container()
    table = document.createElement('table')
    table.id = "order-file-list-table"
    table.innerHTML = file_list_table_template.render(file_items=new_rows)
    container = document.getElementById("order-file-list-table-container")
    container.appendChild(table)


async def upload_order_file(e):
    file_list = e.target.files
    names = [f.name for f in file_list]
    window.console.log("Files uploaded: " + ','.join(names))
    _order_files.update({f.name: await get_bytes_from_file(f) for f in file_list})
    refresh_table_from_order_files()


if __name__ == "__main__":
    # Initialize Order list table.
    initialize_order_list_table()
    # upload_file =
    document.getElementById("order-file-upload").addEventListener(
        "change", create_proxy(upload_order_file)
    )
