from merge_order import (
    download_current_order_variable_settings,
    refresh_order_variable_preview,
    reset_order_variable_settings,
    upload_new_order_variable_settings,
)
from order_file_io import initialize_order_list_table, upload_order_file
from pyscript import document, when

# We are using ``when`` instead of ``create_proxy`` so that we don't have to handle
# garbagae collections of proxies.
# See https://docs.pyscript.net/2024.10.1/user-guide/ffi/#create_proxy for details.


if __name__ == "__main__":
    # Initialize Order list table.
    initialize_order_list_table()
    # Try Loading Order Variable Settings.
    refresh_order_variable_preview()
    # Order file upload button event listener
    when("change", document.getElementById("order-file-upload"))(upload_order_file)
    # Order related setting input/buttons event listeners
    new_order_setting_button = document.getElementById("new-order-variables-button")
    when("change", new_order_setting_button)(upload_new_order_variable_settings)
    download_setting_button = document.getElementById("download-order-variables-button")
    when("click", download_setting_button)(download_current_order_variable_settings)
    reset_order_button = document.getElementById("reset-order-variables-button")
    when("click", reset_order_button)(reset_order_variable_settings)
