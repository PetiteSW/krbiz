from delivery_form import (
    download_current_delivery_format_setting,
    download_orders_in_delivery_format,
    refresh_delivery_format_file_preview,
    refresh_delivery_format_setting_view,
    reset_delivery_format_settings,
    upload_new_delivery_format_settings,
)
from merge_order import download_merged_orders, refresh_merge_file_preview
from order_file_io import initialize_order_list_table, upload_order_file
from order_settings import (
    download_current_order_variable_settings,
    refresh_order_variable_setting_view,
    reset_order_variable_settings,
    upload_new_order_variable_settings,
)
from pyscript import document, when

# We are using ``when`` instead of ``create_proxy`` so that we don't have to handle
# garbagae collections of proxies.
# See https://docs.pyscript.net/2024.10.1/user-guide/ffi/#create_proxy for details.


if __name__ == "__main__":
    # Initialize Order list table.
    initialize_order_list_table()
    # Refresh previews.
    refresh_merge_file_preview()
    refresh_order_variable_setting_view()
    refresh_delivery_format_file_preview()
    refresh_delivery_format_setting_view()
    # Order file upload button
    when("change", document.getElementById("order-file-upload"))(upload_order_file)
    # Order related setting input/buttons
    refresh_button = document.getElementById("merge-preview-refresh")
    when("click", refresh_button)(refresh_merge_file_preview)
    new_order_setting_button = document.getElementById("new-order-variables-button")
    when("change", new_order_setting_button)(upload_new_order_variable_settings)
    download_setting_button = document.getElementById("download-order-variables-button")
    when("click", download_setting_button)(download_current_order_variable_settings)
    reset_order_button = document.getElementById("reset-order-variables-button")
    when("click", reset_order_button)(reset_order_variable_settings)
    # Delivery format setting buttons
    d_setting_upload_btn = document.getElementById("new-delivery-format-button")
    when("change", d_setting_upload_btn)(upload_new_delivery_format_settings)
    d_setting_download_btn = document.getElementById("download-delivery-format-button")
    when("click", d_setting_download_btn)(download_current_delivery_format_setting)
    delivery_format_preview_button = document.getElementById("delivery-preview-refresh")
    when("click", delivery_format_preview_button)(refresh_delivery_format_file_preview)
    reset_delivery_format_button = document.getElementById("reset-delivery-format-button")
    when("click", reset_delivery_format_button)(reset_delivery_format_settings)
    # Merge order download button
    merged_download_button = document.getElementById("merged-orders-download-button")
    when("click", merged_download_button)(download_merged_orders)
    # Delivery format download button
    delivery_button_id = "delivery-format-orders-download-button"
    delivery_format_download_button = document.getElementById(delivery_button_id)
    when("click", delivery_format_download_button)(download_orders_in_delivery_format)
