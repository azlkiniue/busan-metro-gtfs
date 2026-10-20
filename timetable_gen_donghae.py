import csv
import io
import re
import zipfile
import requests
from lxml import etree
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Donghae Line (Bujeon - Taehwagang) electric train timetable published by Korail as an xlsx file
# "동해선 전동열차 시각표(2026.9.1.부터)" listed on https://www.korail.com/ticket/reserve/train-timeTable
url = "https://www.korail.com/file/cubedata/COMMON/jfile/202608/28/202608281a045c826ce180.xlsx"
line = "Donghae"
# station name used in the xlsx -> station code, korean name, english name
station_lookup = {
    "부전": ("K110", "부전", "Bujeon"),
    "거제해": ("K111", "거제해맞이", "Geojehaemaji"),
    "거제": ("K112", "거제", "Geoje"),
    "부교대": ("K113", "교대", "Busan Nat'l Univ. of Edu."),
    "동래": ("K114", "동래", "Dongnae"),
    "안락": ("K115", "안락", "Allak"),
    "부산원": ("K116", "부산원동", "Busanwondong"),
    "재송": ("K117", "재송", "Jaesong"),
    "센텀": ("K118", "센텀", "Centum"),
    "벡스코": ("K119", "벡스코", "BEXCO"),
    "신해운": ("K120", "신해운대", "Sinhaeundae"),
    "송정": ("K121", "송정", "Songjeong"),
    "오시리": ("K122", "오시리아", "OSIRIA"),
    "기장": ("K123", "기장", "Gijang"),
    "일광": ("K124", "일광", "Ilgwang"),
    "좌천": ("K125", "좌천", "Jwacheon"),
    "월내": ("K126", "월내", "Wollae"),
    "서생": ("K127", "서생", "Seosaeng"),
    "남창": ("K128", "남창", "Namchang"),
    "망양": ("K129", "망양", "Mangyang"),
    "덕하": ("K130", "덕하", "Deokha"),
    "개운포": ("K131", "개운포", "Gaeunpo"),
    "태화강": ("K132", "태화강", "Taehwagang"),
}
# sheet name -> day codes and updown code, same as timetable.csv
# (day 1: weekday, 2: saturday, 3: sunday/holiday, updown 1: toward Taehwagang, 0: toward Bujeon)
# the holiday (휴일) timetable of Korail is used on saturday, sunday and public holidays
sheet_lookup = {
    "평일 하행": (["1"], "1"),
    "평일 상행": (["1"], "0"),
    "휴일 하행": (["2", "3"], "1"),
    "휴일 상행": (["2", "3"], "0"),
}
ns = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def request_file(url):
    # download the xlsx file, create backoff strategy and retry
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    response = session.get(url)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        exit()
    return response.content


def read_sheets(content):
    # read every sheet of the xlsx file into a dictionary of (row, column) -> value
    xlsx = zipfile.ZipFile(io.BytesIO(content))
    shared_strings = []
    if "xl/sharedStrings.xml" in xlsx.namelist():
        root = etree.fromstring(xlsx.read("xl/sharedStrings.xml"))
        for item in root.findall("m:si", ns):
            shared_strings.append("".join(item.itertext()))
    workbook = etree.fromstring(xlsx.read("xl/workbook.xml"))
    relations = etree.fromstring(xlsx.read("xl/_rels/workbook.xml.rels"))
    targets = {
        relation.get("Id"): relation.get("Target")
        for relation in relations.findall("rel:Relationship", ns)
    }

    sheets = {}
    for sheet in workbook.find("m:sheets", ns).findall("m:sheet", ns):
        target = targets[sheet.get("{%s}id" % ns["r"])].lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        root = etree.fromstring(xlsx.read(target))
        cells = {}
        for cell in root.iter("{%s}c" % ns["m"]):
            reference = re.match(r"([A-Z]+)(\d+)", cell.get("r"))
            column = 0
            for letter in reference.group(1):
                column = column * 26 + ord(letter) - 64
            value = cell.find("m:v", ns)
            if value is None:
                continue
            if cell.get("t") == "s":
                cells[(int(reference.group(2)), column)] = shared_strings[int(value.text)]
            else:
                cells[(int(reference.group(2)), column)] = value.text
        sheets[sheet.get("name")] = cells
    return sheets


def format_time(seconds):
    hour, rest = divmod(seconds, 3600)
    minute, second = divmod(rest, 60)
    return f"{str(hour).zfill(2)}:{str(minute).zfill(2)}:{str(second).zfill(2)}"


def parse_sheet(cells, days, updown):
    # row 2: origin station, row 3: destination station, row 4: train number
    # from row 5, every station has two rows: arrival time (with station name) and departure time
    # times are written as a fraction of a day
    last_row = max(row for row, column in cells)
    last_column = max(column for row, column in cells)
    stations = [
        (row, cells[(row, 1)].strip())
        for row in range(5, last_row + 1)
        if cells.get((row, 1), "").strip()
    ]

    schedules = []
    for column in range(2, last_column + 1):
        trainno = cells.get((4, column), "").strip()
        if not trainno:
            continue
        endcode = station_lookup[cells[(3, column)].strip()][0]
        for row, name in stations:
            arrival = cells.get((row, column), "").strip()
            departure = cells.get((row + 1, column), "").strip()
            if not arrival and not departure:
                continue
            times = []
            for value in (arrival or departure, departure or arrival):
                seconds = round(float(value) * 86400)
                # trains after midnight belong to the previous service day (first train is at 05:20)
                if seconds < 4 * 3600:
                    seconds += 24 * 3600
                times.append(seconds)
            scode, sname, engname = station_lookup[name]
            for day in days:
                schedules.append(
                    {
                        "scode": scode,
                        "sname": sname,
                        "engname": engname,
                        "trainno": trainno,
                        "day": day,
                        "updown": updown,
                        "endcode": endcode,
                        "arrival": times[0],
                        "departure": times[1],
                    }
                )
    return schedules


def write_to_csv(schedules):
    # write the data to a csv file with the same columns as timetable.csv,
    # plus the exact arrival and departure time published by Korail
    with open("timetable_donghae.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "scode",
                "line",
                "sname",
                "engname",
                "trainno",
                "hour",
                "time",
                "day",
                "updown",
                "endcode",
                "arrival",
                "departure",
            ]
        )
        # sort the same way as timetable.csv: station, day, direction, time
        schedules.sort(
            key=lambda x: (x["scode"], x["day"], x["updown"], x["departure"])
        )
        for schedule in schedules:
            departure = format_time(schedule["departure"])
            writer.writerow(
                [
                    schedule["scode"],
                    line,
                    schedule["sname"],
                    schedule["engname"],
                    schedule["trainno"],
                    departure[0:2],
                    departure[3:5],
                    schedule["day"],
                    schedule["updown"],
                    schedule["endcode"],
                    format_time(schedule["arrival"]),
                    departure,
                ]
            )


sheets = read_sheets(request_file(url))
schedules = []
for sheet_name, (days, updown) in sheet_lookup.items():
    schedules.extend(parse_sheet(sheets[sheet_name], days, updown))

write_to_csv(schedules)
print(f"Generated timetable_donghae.csv with {len(schedules)} rows.")
