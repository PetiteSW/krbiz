import json
from collections.abc import Callable
from dataclasses import dataclass

from js import confirm
from order_settings import load_order_variables_from_local_storage
from pyscript import document, when, window

_DELIVERY_INFO_KEY_SETTING_LOCAL_STORAGE_KEY = "DELIVERY-INFO-KEYS"


@dataclass
class DeliveryInfoKey:
    unified_variable_name: str
    """Unified variable name. i.e. receipients_name"""
    delivery_info_header: str
    """Header of the delivery information. i.e. 수하인명"""


@dataclass
class DeliveryInfoKeysRegistry:
    """Proxy to the local storage."""
    keys: tuple[DeliveryInfoKey, ...]

    def add_key(self, delivery_info_header: str, unified_variable_name: str) -> None:
        new_key = DeliveryInfoKey(
            delivery_info_header=delivery_info_header,
            unified_variable_name=unified_variable_name,
        )
        # Make sure same delivery info header does not exist.
        self.delete_key(delivery_info_header)
        self.keys = (new_key, *self.keys)
        self._save_to_local_storage()
        refresh_delivery_info_keys_table()

    def delete_key(self, delivery_info_header: str) -> None:
        self.keys = tuple(
            key for key in self.keys if key.delivery_info_header != delivery_info_header
        )
        self._save_to_local_storage()

    def _save_to_local_storage(self) -> None:
        self_as_dict = {
            key.delivery_info_header: key.unified_variable_name for key in self.keys
        }
        _update_delivery_info_keys_in_local_storage(self_as_dict)


def initialize_delivery_key_format() -> None:
    unified_variables = load_order_variables_from_local_storage()
    select_input = document.getElementById("unified-variable-key-selection")
    select_input.replaceChildren()
    for var in unified_variables.unified_header:
        new_opt = document.createElement('option')
        new_opt.value = var
        new_opt.innerHTML = var
        select_input.appendChild(new_opt)


def add_delivery_info_key(event=None) -> None:
    if event:
        event.preventDefault()  # Don't know why it is needed,
        # but otherwise it raises error in javascript layer.
        delivery_header_input = document.getElementById("delivery-info-header-key")
        delivery_header_val = delivery_header_input.value
        unified_variable_input = document.getElementById(
            "unified-variable-key-selection"
        )
        unified_variable_val = unified_variable_input.value
        key_registry = load_delivery_info_keys_from_local_storage()
        key_registry.add_key(delivery_header_val, unified_variable_val)
        window.console.log(
            f"New delivery info keys: {delivery_header_val} - {unified_variable_val}"
        )

        # Reset input fields.
        delivery_header_input.value = ""
        if unified_variable_input.children:
            first_child = next(iter(unified_variable_input.children))
            unified_variable_input.value = first_child.value


def _update_delivery_info_keys_in_local_storage(
    new_vars_to_header: dict[str, str],
) -> None:
    window.console.log("Updating delivery info keys in the local storage...")
    local_storage = window.localStorage
    if local_storage.getItem(_DELIVERY_INFO_KEY_SETTING_LOCAL_STORAGE_KEY) is not None:
        window.console.log("Overwriting the existing delivery info keys.")
    delivery_keys_str = json.dumps(new_vars_to_header, ensure_ascii=False)
    local_storage.setItem(
        _DELIVERY_INFO_KEY_SETTING_LOCAL_STORAGE_KEY, delivery_keys_str
    )


def _initialize_delivery_info_keys_in_local_storage() -> None:
    window.console.log("Initializing delivery info keys as defaults.")
    default_vars_to_header = {"수하인명": "receipients_name", "상품명": "product_name"}
    _update_delivery_info_keys_in_local_storage(default_vars_to_header)


def load_delivery_info_keys_from_local_storage() -> DeliveryInfoKeysRegistry:
    local_storage = window.localStorage
    if local_storage.getItem(_DELIVERY_INFO_KEY_SETTING_LOCAL_STORAGE_KEY) is None:
        _initialize_delivery_info_keys_in_local_storage()
    else:
        window.console.log("Found the existing delivery keys.")
    try:
        order_variables_dict = json.loads(
            local_storage.getItem(_DELIVERY_INFO_KEY_SETTING_LOCAL_STORAGE_KEY)
        )
        window.console.log(str(order_variables_dict))
        return DeliveryInfoKeysRegistry(
            keys=tuple(
                DeliveryInfoKey(
                    unified_variable_name=unified_var,
                    delivery_info_header=delivery_header,
                )
                for delivery_header, unified_var in order_variables_dict.items()
            )
        )
    except Exception:
        window.console.log(
            "Error occurred while loading existing delivery info keys. "
            "Please reset the settings."
        )


def _make_button_id(delivery_header: str) -> str:
    return f"delivery-key-{delivery_header}-delete-button"


def _make_delete_button(delivery_header: str) -> str:
    button_id = _make_button_id(delivery_header)
    button_tag = (
        '<div class="little-button-box"><button type="button" class="delete-button" '
        + f'id="{button_id}" value="{delivery_header}">'
    )
    trash_icon = '<img src="trash_icon.png" alt="🗑️" height=1em>'
    return f'{button_tag}{trash_icon}</button></div>'


def make_delete_button_event_listener(delivery_header: str) -> Callable:
    def _delete_it(_) -> None:
        if confirm("선택하신 열 이름 짝을 삭제하시겠습니까?") and confirm(
            "진짜 지워요? 🤔"
        ):
            key_registry = load_delivery_info_keys_from_local_storage()
            key_registry.delete_key(delivery_header)
            window.console.log(f"Deleted {delivery_header}")
            refresh_delivery_info_keys_table()
        else:
            window.console.log(f"Canceled deleting {delivery_header}")

    return _delete_it


def refresh_delivery_info_keys_table(_=None) -> None:
    key_registry = load_delivery_info_keys_from_local_storage()
    rows = [
        '<tr>'
        f'<td class="short-column">{key.delivery_info_header}</td>'
        f'<td class="short-column">{key.unified_variable_name}</td>'
        f'<td class="short-column">{_make_delete_button(key.delivery_info_header)}</td>'
        '</tr>'
        for key in key_registry.keys
    ]
    table_str = f"""
        <table>
            <tr class="header-row">
                <td> 배송정보 열 이름 </td>
                <td> 통합 열 이름 </td>
                <td> 삭제 </td>
            </tr>
            {'\n'.join(rows)}
        </table>
    """
    viewer_box = document.getElementById("delivery-info-keys-viewer-box")
    viewer_box.replaceChildren()
    new_table = document.createElement('table')
    new_table.innerHTML = table_str
    viewer_box.appendChild(new_table)
    # Add delete button event listeners
    for key in key_registry.keys:
        button_id = _make_button_id(key.delivery_info_header)
        del_button = document.getElementById(button_id)
        when("click", del_button)(
            make_delete_button_event_listener(key.delivery_info_header)
        )
