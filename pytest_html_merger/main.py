import re
import argparse
import os
from bs4 import BeautifulSoup
import sys
import pathlib


CUR_PATH = "{0}/".format(os.path.dirname(__file__))

sys.path.append(CUR_PATH)

import version as version_mod


CHECKBOX_REGEX = r"^(?P<num>0|[1-9]\d*) (?P<txt1>.*)"


def merge_html_files(in_path, out_path, title):
    paths = get_html_files(in_path)
    if not paths:
        raise RuntimeError(f"Was unable to find html files in {in_path}")

    assets_dir_path = get_assets_path(in_path)

    first_file = BeautifulSoup("".join(open(paths[0])), features="html.parser")

    main_table = BeautifulSoup("<table id='results-table'><tbody></tbody></table>")

    try:
        first_file.find("link").decompose()
    except:
        pass

    if assets_dir_path is None:
        print(
            f"Will assume css is embedded in the reports. If this is not the case, "
            f"Please make sure that you have 'assets' directory inside {in_path} "
            f"which contains css files generated by pytest-html."
        )
    else:
        with open(os.path.join(assets_dir_path, "style.css"), "r") as f:
            content = f.read()

            head = first_file.head
            head.append(first_file.new_tag("style", type="text/css"))
            head.style.append(content)

    _title = title if title else os.path.basename(out_path)
    h = first_file.find("h1")
    case_title = h.string
    h.string = _title
    t = first_file.find("title")
    t.string = _title

    t = first_file.find("table", {"id": "results-table"})
    t.id = "results-table-0"

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
    if cb_types['failed'][0] > 0:
        status = 'Failed'
    elif cb_types["passed"][0] > 0:
        status = 'Passed'
    elif cb_types["skipped"][0] > 0:
        status = 'Skipped'
    
    main_table.find('tbody').append(f'<tr><td>{case_title}</td><td>{status}</td><td>{dur}</td></tr><tr><td colspan="3" class="case-report-result">{t}</td></tr>')

    for path in paths:
        if path == paths[0]:
            continue

        second_file = BeautifulSoup("".join(open(path)), features="html.parser")
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

        if current_cb_types['failed'][0] > 0:
            status = 'Failed'
        elif current_cb_types["passed"][0] > 0:
            status = 'Passed'
        elif current_cb_types["skipped"][0] > 0:
            status = 'Skipped'

        res = second_file.find_all("talbe", {"id": "results-table"})

        main_table.find('tbody').append(f'<tr><td>{case_title}</td><td>{status}</td><td>{current_case_duration}</td></tr><tr><td colspan="3" class="case-report-result">{res}</td></tr>')

    first_file.find("table", {"id": "results-table"}).replace_with(main_table)
    res = first_file.find_all("p")
    for p in res:
        if " tests ran" in p.text:
            p.string = f"{test_count} tests ran in {dur} seconds"

            break

    for cb_type in cb_types:
        set_checkbox_value(first_file, cb_type, cb_types[cb_type])

    with open(out_path, "w") as f:
        f.write(str(first_file))


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

    args = parser.parse_args(command_line)

    return args


def main(command_line=None):
    args = parse_user_commands(command_line)

    merge_html_files(args.input, args.output, args.title)


if __name__ == "__main__":
    main()
