from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("juriscraper", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)
