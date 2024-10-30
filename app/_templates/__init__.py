from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
import pathlib

_env = Environment(
    loader=FileSystemLoader(pathlib.Path(__file__).parent),
    autoescape=select_autoescape(),
)
file_list_table_template = _env.get_template("order-file-table.html.jinja")
file_item_row_template = _env.get_template("order-file-list-item.html.jinja")
merge_preview_template = Template(
    '''
<table>
    <tr class="header-row">
        <td class="index-column">{% for item in header_items %}{{item}}</td>
        {% if not loop.last %}<td>{% endif %}{% endfor %}
    </tr>
    {% for row in rows %}<tr>
        <td class="index-column">{% for item in row %}{{item}}</td>
        {% if not loop.last %}<td>{% endif %}{% endfor %}
    </tr>{% endfor %}
</table>
'''
)
delivery_format_setting_template = Template(
    '''
<table>
    <tr class="header-row">
        {% for item in header_items %}<td>{{item}}</td>{% endfor %}
    </tr>
    <tr>
        {% for item in templates %}<td>{{item}}</td>{% endfor %}
    </tr>
</table>
'''
)
delivery_format_preview_template = Template(
    '''
<table>
    <tr class="header-row">
        <td class="index-column">{% for item in header_items %}{{item}}</td>
        {% if not loop.last %}<td>{% endif %}{% endfor %}
    </tr>
    {% for row in rows %}<tr>
        <td class="index-column">{% for item in row %}{{item}}</td>
        {% if not loop.last %}<td>{% endif %}{% endfor %}
    </tr>{% endfor %}
</table>
'''
)

delivery_split_table_template = _env.get_template("delivery-split-table.html.jinja")
delivery_split_row_template = _env.get_template("delivery-split-list-item.html.jinja")
