from datetime import datetime

import jinja2

from juriscraper.templates import env as jinja_env


def generate_scraper_report(file_path, results):
    no_error = []
    with_errors = []
    with_zero_results = []
    with_global_failure = []
    for name, scraper in results.items():
        has_error = False
        if scraper["global_failure"]:
            with_global_failure.append(name)
            has_error = True
        scrape = scraper["scrape"]
        if scrape.get("count") == 0:
            with_zero_results.append(name)
            has_error = True
        for exc in scrape.get("exceptions", []):
            if len(exc) > 0:
                with_errors.append(name)
                has_error = True
                break
        if not has_error:
            no_error.append(name)

    display = {
        "generated_on": datetime.now().strftime("%a, %B %d %Y %H:%M:%S"),
        "count": len(results),
        "no_error": no_error,
        "with_errors": with_errors,
        "with_zero_results": with_zero_results,
        "with_global_failure": with_global_failure,
        "total_errors": len(with_errors)
        + len(with_zero_results)
        + len(with_global_failure),
    }
    template = jinja_env.get_template(
        "juriscraper/templates/report.html.jinja2"
    )
    with open(file_path, "w") as f:
        f.write(template.render(display))
