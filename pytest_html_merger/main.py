import re
import argparse
import os
from bs4 import BeautifulSoup
import sys
import pathlib
import pkg_resources
import json

from helpers import CaseStatuses, CaseStatusData


CUR_PATH = "{0}/".format(os.path.dirname(__file__))

sys.path.append(CUR_PATH)

import version as version_mod


CHECKBOX_REGEX = r"^(?P<num>0|[1-9]\d*) (?P<txt1>.*)"


def merge_html_files(in_path, out_path, title, log_data):
    paths = get_html_files(in_path)
    if not paths:
        raise RuntimeError(f"Was unable to find html files in {in_path}")

    css_resource_path = pkg_resources.resource_filename(__name__, 'resources/style.css').encode()
    with open(css_resource_path.decode(), 'r') as style:
        css_styles = style.read()
        report_style = f"<style>{css_styles}</style>"
        style_soup = BeautifulSoup(report_style, 'html.parser').find('style')

    js_resource_path = pkg_resources.resource_filename(__name__, 'resources/report.js').encode()
    with open(js_resource_path.decode(), 'r') as js_file:
        js = js_file.read()
        report_js = f"<script>{js}</script>"
        js_soup = BeautifulSoup(report_js, 'html.parser').find('script')

    assets_dir_path = get_assets_path(in_path)

    first_file = BeautifulSoup("".join(open(paths[0])), features="html.parser")
    first_file.script.clear()

    try:
        first_file.find("link").decompose()
    except:
        pass

    # if assets_dir_path is None:
    #     print(
    #         f"Will assume css is embedded in the reports. If this is not the case, "
    #         f"Please make sure that you have 'assets' directory inside {in_path} "
    #         f"which contains css files generated by pytest-html."
    #     )
    # else:
    #     with open(os.path.join(assets_dir_path, "style.css"), "r") as f:
    #         content = f.read()

    #         head = first_file.head
    #         head.append(first_file.new_tag("style", type="text/css"))
    #         head.style.append(content)

    first_file.find('head').append(style_soup)
    first_file.find('body').append(js_soup)

    _title = title if title else os.path.basename(out_path)
    h = first_file.find("h1")
    case_title = h.string
    h.string = _title
    t = first_file.find("title")
    t.string = _title

    t = first_file.find("table", {"id": "results-table"})
    # t.id = "results-table-0"

    cb_types = {
        "passed": [0, ""],
        "skipped": [0, ""],
        "failed": [0, ""],
        "error": [0, ""],
        "xfailed": [0, ""],
        "xpassed": [0, ""],
    }

    for cb_type in cb_types:
        tmp = get_checkbox_value(first_file, cb_type)
        cb_types[cb_type][0] = tmp[0]
        cb_types[cb_type][1] = tmp[1]

    test_count = 0
    dur = 0
    ps = first_file.find_all("p")
    for p in ps:
        if " tests ran" in p.text:
            tmp = p.text.split(" ")
            test_count = int(tmp[0])
            dur = float(tmp[4])

            break
    
    new_table = '<div id="results-table"></div>'
    new_table_soup = BeautifulSoup(new_table, 'html.parser').find('div', {"id": "results-table"})

    js_log_data = {}
    log_key = case_title.replace('report', '').strip().replace(' ', '_').lower()
    js_log_data[log_key] = get_log_data(log_data[log_key])
    
    new_case_soup = create_case_container(first_file, case_title, dur, log_data, log_key) # first_file
    new_table_soup.append(new_case_soup)

    for i in range(len(paths)):
        path = paths[i]
        if path == paths[0]:
            continue

        second_file = BeautifulSoup("".join(open(path)), features="html.parser")
        h = second_file.find("h1")
        case_title = h.string
        # for elm in res:
        #     t.append(elm)

        res = second_file.find_all("p")
        current_case_duration = 0
        for p in res:
            if " tests ran" in p.text:
                tmp = p.text.split(" ")
                test_count += int(tmp[0])
                dur += float(tmp[4])
                current_case_duration += float(tmp[4])

                break
        
        current_cb_types = {
            "passed": [0, ""],
            "skipped": [0, ""],
            "failed": [0, ""],
            "error": [0, ""],
            "xfailed": [0, ""],
            "xpassed": [0, ""],
        }
        for cb_type in cb_types:
            tmp = get_checkbox_value(second_file, cb_type)
            cb_types[cb_type][0] += tmp[0]
            current_cb_types[cb_type][0] = tmp[0]
        
        log_key = case_title.replace('report', '').strip().replace(' ', '_').lower()
        js_log_data[log_key] = get_log_data(log_data[log_key])

        new_case_soup = create_case_container(second_file, case_title, current_case_duration, log_data, log_key, i)
        new_table_soup.append(new_case_soup)

    first_file.body.append(new_table_soup)
    res = first_file.find_all("p")
    for p in res:
        if " tests ran" in p.text:
            p.string = f"{test_count} tests ran in {dur} seconds"

            break

    for cb_type in cb_types:
        set_checkbox_value(first_file, cb_type, cb_types[cb_type])

    log_data_script = f"const LOG_DATA={json.dumps(js_log_data)};"
    log_data_script_soup = BeautifulSoup(f'<script>{log_data_script}</script>', 'html.parser').find('script')
    first_file.head.append(log_data_script_soup)

    first_file.body.append(get_modal())

    with open(out_path, "w") as f:
        f.write(str(first_file))

def create_case_container(soup: BeautifulSoup, title, current_case_duration, log_data, log_key, index = 1):
    result_table = soup.find('table', {"id": "results-table"})
    result_table.attrs = {**result_table.attrs, "id": f'results-table-{index}', 'class': 'results-table'}

    new_case = '<div class="case-row"></div>'
    new_headers = '<div class="case-row-headers"></div>'
    new_results_row = '<div class="case-row-results"></div>'
    case_log_item = '<span class="case-log"></span>'
    
    new_results_row_soup = BeautifulSoup(new_results_row, 'html.parser')
    new_results_row_soup.find('div', {"class": "case-row-results"}).append(result_table)
    
    new_headers_soup = BeautifulSoup(new_headers, 'html.parser').find('div', {"class": "case-row-headers"})

    status_data = get_case_status(result_table)
    new_headers_soup.attrs['class'] = [*new_headers_soup.attrs['class'], status_data.get("class_name", CaseStatuses.FAILED.value.lower())]
    status_title = status_data.get('title', CaseStatuses.FAILED.value)
    
    # add title column
    new_header_item_soup = get_header_item('title')
    new_header_item_soup.string = title
    new_headers_soup.append(new_header_item_soup)

    # add status column
    new_header_item_soup = get_header_item('status')
    new_header_item_soup.string = status_title
    new_headers_soup.append(new_header_item_soup)
    
    # add duration column
    new_header_item_soup = get_header_item('duration')
    new_header_item_soup.string = f'{current_case_duration}'
    new_headers_soup.append(new_header_item_soup)
    
    # add logs column
    new_header_item_soup = get_header_item('logs')
    for log in log_data[log_key]:
        case_log_item_soup = BeautifulSoup(case_log_item, 'html.parser').span
        case_log_item_soup.attrs['onclick'] = f'javascript:showLog(this, "{log_key}")'
        case_log_item_soup.string = log.split('/')[-1]
        new_header_item_soup.append(case_log_item_soup)
    new_headers_soup.append(new_header_item_soup)
    

    new_case_soup = BeautifulSoup(new_case, 'html.parser').find('div', {"class": "case-row"})
    new_case_soup.append(new_headers_soup)
    new_case_soup.append(new_results_row_soup)

    return new_case_soup

def get_header_item(className = ''):
    new_header_item = '<div class="case-row-headers__item"></div>'
    soup = BeautifulSoup(new_header_item, 'html.parser').find('div', {"class": "case-row-headers__item"})
    if className:
        soup.attrs['class'] = [*soup.attrs['class'], className]
    return soup

def get_case_status(soup: BeautifulSoup):
    results = soup.find_all('td', {'class': 'col-result'})
    statuses = [td.string.upper() for td in results]
    
    is_failed = any([CaseStatuses.FAILED.value.lower() == status.lower() for status in statuses])
    if is_failed:
        return CaseStatusData.get_failed_data()
    
    is_passed = any([CaseStatuses.PASSED.value.lower() == status.lower() for status in statuses])
    if is_passed:
        return CaseStatusData.get_passed_data()
    
    is_skipped = all([CaseStatuses.SKIPPED.value.lower() == status.lower() for status in statuses])
    if is_skipped:
        return CaseStatusData.get_skipped_data()
    
    is_expected_failures = any([CaseStatuses.EXPECTED_FAILURES.value.lower() == status.lower() for status in statuses])
    if is_expected_failures:
        return CaseStatusData.get_expected_faileres_data()
    
    is_unexpected_passes = any([CaseStatuses.UNEXPECTED_PASSES.value.lower() == status.lower() for status in statuses])
    if is_unexpected_passes:
        return CaseStatusData.get_unexpected_passes_data()
    
    return {}

def get_modal():
    modal = '''<div id="modal">
    <div class="modal-container">
    <div class="modal-header"><span id="log-title"></span><span id="close-modal">+</span></div>
    <code id="modal-content"></code>
    </div>
    </div>'''
    return BeautifulSoup(modal,'html.parser').find('div', {'id': 'modal'})

def get_log_data(log_data):
    logs = {}
    for log in log_data:
        log_key = log.split('/')[-1]
        with open(log, 'r') as l:
            logs[log_key] = l.read()
    
    return logs

def set_checkbox_value(root_soap, cb_type, val):
    elem = root_soap.find("span", {"class": cb_type})
    match = re.search(CHECKBOX_REGEX, elem.text)
    if match is None:
        raise RuntimeError(f"{cb_type} <span> not found")

    elem.string = f"{val[0]} {val[1]}"

    elem = root_soap.find("input", {"data-test-result": cb_type})
    if val[0] != 0:
        del elem["disabled"]
        del elem["hidden"]


def get_checkbox_value(root_soap, cb_type):
    elem = root_soap.find("span", {"class": cb_type})
    match = re.search(CHECKBOX_REGEX, elem.text)
    if match is None:
        raise RuntimeError(f"{cb_type} <span> not found")

    gdict = match.groupdict()

    return int(gdict["num"]), gdict["txt1"]


def get_html_files(path):
    onlyfiles = []

    for p in pathlib.Path(path).rglob("*.html"):
        res = str(p.absolute())
        if "merged.html" in res:
            continue

        tmp = BeautifulSoup("".join(open(res)), features="html.parser")
        p = tmp.find("p")
        if p and "Report generated on " in p.text:
            onlyfiles.append(res)

    return onlyfiles


def get_assets_path(path):
    res = None

    for p in pathlib.Path(path).rglob("assets"):
        return str(p.absolute())

    return res


def parse_user_commands(command_line):
    parser = argparse.ArgumentParser("pytest_html_merger")

    parser.add_argument(
        "--version", "-v", action="version", version=version_mod.version
    )

    parser.add_argument(
        "-i",
        "--input",
        default=os.path.abspath(os.path.dirname(__file__)),
        help="",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=os.path.join(os.path.abspath(os.path.dirname(__file__)), "merged.html"),
        help="",
    )
    parser.add_argument(
        "-t",
        "--title",
        default='',
        help="Merged report title",
    )
    parser.add_argument(
        "-l",
        "--log",
        default='',
        help="Merged report logs data",
    )

    args = parser.parse_args(command_line)

    return args


def main(command_line=None):
    args = parse_user_commands(command_line)

    merge_html_files(args.input, args.output, args.title, json.loads(args.log))


if __name__ == "__main__":
    main()
