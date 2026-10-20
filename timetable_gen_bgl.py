import csv
import requests
from lxml import html
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# station timetable page of the Busan-Gimhae Light Rail Transit (BGL) operator website
url = "https://www.bglrt.com/00011/00149.web"
line = "BGL"
# station code used by the operator website, from Sasang (901) to Kaya Univ. (921)
scode_list = [i for i in range(901, 922)]
# english station names as written on the operator's line map
engname_lookup = {
    901: "Sasang",
    902: "Gwaebeop Renecite",
    903: "Seobusan Yutongjigu",
    904: "Gimhae International Airport",
    905: "Deokdu",
    906: "Deunggu",
    907: "Daejeo",
    908: "Pyeonggang",
    909: "Daesa",
    910: "Buram",
    911: "Jinae",
    912: "Gimhae College",
    913: "Inje Univ.",
    914: "Gimhae City Hall",
    915: "Buwon",
    916: "Bonghwang",
    917: "Royal Tomb of King Suro",
    918: "Gimhae National Museum",
    919: "Yeonji Park",
    920: "Presbyterian Univ.",
    921: "Kaya Univ.",
}
# the timetable has weekday (평일), saturday (토요일) and holiday (휴일) columns
# use the same day code as timetable.csv (1: weekday, 2: saturday, 3: sunday/holiday)
day_list = ["1", "2", "3"]
# terminal of each direction tab, use the same updown code as timetable.csv
# 1: toward Kaya Univ. (increasing station code), 0: toward Sasang
direction_lookup = {
    "가야대": ("1", 921),
    "사상": ("0", 901),
}


def request_page(url, params):
    # make a request to the website, create backoff strategy and retry
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    # the website rejects the default user agent of requests
    headers = {"User-Agent": "busan-metro-gtfs (+https://github.com/azlkiniue/busan-metro-gtfs)"}
    response = session.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        exit()
    return response


def parse_response(response, scode):
    # the page has one tab for each direction, e.g. "가야대(삼계)행" and "사상(서부터미널)행"
    # each tab has a first/last train table and a full timetable (전체운행시간표) table
    # every row of the full timetable is: hour, weekday minutes, saturday minutes, holiday minutes
    root = html.fromstring(response.content)
    sname = root.xpath('string(//div[@id="tabs2a1pane1"]/h3/span[@class="t1"])')
    # drop the sub name in parentheses, e.g. "사상(서부터미널)" -> "사상"
    sname = sname.split("(")[0].strip()

    schedules = []
    for pane in root.xpath('//div[@class="tabs3a1pane"]'):
        label = pane.xpath("string(h4)").strip()
        terminal = [key for key in direction_lookup if label.startswith(key)]
        if not terminal:
            print(f"Error: unknown direction {label} (scode: {scode})")
            exit()
        updown, endcode = direction_lookup[terminal[0]]

        table = pane.xpath('.//h5[contains(., "전체운행시간표")]/following-sibling::table[1]')[0]
        for row in table.xpath("./tbody/tr"):
            cells = [td.text_content().split() for td in row.xpath("./td")]
            if len(cells) != 4:
                continue
            hour = cells[0][0]
            for day, minutes in zip(day_list, cells[1:]):
                for minute in minutes:
                    schedules.append(
                        {
                            "scode": scode,
                            "sname": sname,
                            "hour": int(hour),
                            "time": int(minute),
                            "day": day,
                            "updown": updown,
                            "endcode": endcode,
                        }
                    )
    return schedules


def service_minutes(schedule):
    # trains after midnight belong to the previous service day (first train is at 05:00)
    hour = schedule["hour"]
    if hour < 4:
        hour += 24
    return hour * 60 + schedule["time"]


def assign_train_numbers(schedules):
    # the website only publishes the departure times of every station without train numbers
    # trains do not overtake each other and every train runs the whole line,
    # so the n-th train at every station of the same day and direction is the same train
    groups = {}
    for schedule in schedules:
        key = (schedule["day"], schedule["updown"])
        groups.setdefault(key, {}).setdefault(schedule["scode"], []).append(schedule)

    for (day, updown), stations in groups.items():
        order = sorted(stations)
        if updown == "0":
            order.reverse()
        for scode in order:
            stations[scode].sort(key=service_minutes)
        counts = {len(stations[scode]) for scode in order}
        if len(counts) != 1:
            print(f"Error: different number of trains in each station (day: {day}, updown: {updown})")
            exit()
        for index in range(counts.pop()):
            trainno = str(index + 1).zfill(3)
            previous = None
            for scode in order:
                schedule = stations[scode][index]
                schedule["trainno"] = trainno
                # running time between two stations is a few minutes
                current = service_minutes(schedule)
                if previous is not None and not 0 < current - previous <= 10:
                    print(f"Error: unexpected running time to {scode} (day: {day}, updown: {updown}, train: {trainno})")
                    exit()
                previous = current


def write_to_csv(schedules):
    # write the data to a csv file with the same columns as timetable.csv
    with open("timetable_bgl.csv", "w", newline="", encoding="utf-8") as f:
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
            ]
        )
        # sort the same way as timetable.csv: station, day, direction, time
        schedules.sort(
            key=lambda x: (x["scode"], x["day"], x["updown"], service_minutes(x))
        )
        for schedule in schedules:
            minutes = service_minutes(schedule)
            writer.writerow(
                [
                    schedule["scode"],
                    line,
                    schedule["sname"],
                    engname_lookup[schedule["scode"]],
                    schedule["trainno"],
                    str(minutes // 60).zfill(2),
                    str(minutes % 60).zfill(2),
                    schedule["day"],
                    schedule["updown"],
                    schedule["endcode"],
                ]
            )


schedules = []
for scode in tqdm(scode_list, desc="Processing", unit="station"):
    response = request_page(url, {"scode": str(scode)})
    schedules.extend(parse_response(response, scode))

assign_train_numbers(schedules)
write_to_csv(schedules)
print(f"Generated timetable_bgl.csv with {len(schedules)} rows.")
