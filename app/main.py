from merge_order import refresh_merge_file_preview
from order_file_io import initialize_order_list_table, upload_order_file
from order_settings import (
    download_current_order_variable_settings,
    refresh_order_variable_preview,
    reset_order_variable_settings,
    upload_new_order_variable_settings,
)
from pyscript import document, when

# We are using ``when`` instead of ``create_proxy`` so that we don't have to handle
# garbagae collections of proxies.
# See https://docs.pyscript.net/2024.10.1/user-guide/ffi/#create_proxy for details.


async def _refresh_merge_file_preview(_):
    import asyncio

    # Work-around to associate new files with the preview.
    await asyncio.sleep(1)
    refresh_merge_file_preview()


if __name__ == "__main__":
    # Initialize Order list table.
    initialize_order_list_table()
    # Refresh previews.
    refresh_order_variable_preview()
    # Order file upload button event listener
    when("change", document.getElementById("order-file-upload"))(upload_order_file)
    # Order related setting input/buttons event listeners
    refresh_button = document.getElementById("merge-preview-refresh")
    when("click", refresh_button)(refresh_merge_file_preview)
    new_order_setting_button = document.getElementById("new-order-variables-button")
    when("change", new_order_setting_button)(upload_new_order_variable_settings)
    download_setting_button = document.getElementById("download-order-variables-button")
    when("click", download_setting_button)(download_current_order_variable_settings)
    reset_order_button = document.getElementById("reset-order-variables-button")
    when("click", reset_order_button)(reset_order_variable_settings)
