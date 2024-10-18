from jinja2 import Environment, FileSystemLoader, select_autoescape
import pathlib

_env = Environment(
    loader=FileSystemLoader(pathlib.Path(__file__).parent),
    autoescape=select_autoescape(),
)
file_list_table_template = _env.get_template("order-file-table.html.jinja")
file_item_row_template = _env.get_template("order-file-list-item.html.jinja")
