import csv
import requests
from lxml import etree
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

url = "http://data.humetro.busan.kr/voc/api/open_api_process.tnn"
service_key = "" # obtain key to this public data from this url https://www.data.go.kr/data/15000522/openapi.do
scode_list = [
    95,
    96,
    97,
    98,
    99,
    100,
    101,
    102,
    103,
    104,
    105,
    106,
    107,
    108,
    109,
    110,
    111,
    112,
    113,
    114,
    115,
    116,
    117,
    118,
    119,
    120,
    121,
    122,
    123,
    124,
    125,
    126,
    127,
    128,
    129,
    130,
    131,
    132,
    133,
    134,
    201,
    202,
    203,
    204,
    205,
    206,
    207,
    208,
    209,
    210,
    211,
    212,
    213,
    214,
    215,
    216,
    217,
    218,
    219,
    220,
    221,
    222,
    223,
    224,
    225,
    226,
    227,
    228,
    229,
    230,
    231,
    232,
    233,
    234,
    235,
    236,
    237,
    238,
    239,
    240,
    241,
    242,
    243,
    301,
    302,
    303,
    304,
    305,
    306,
    307,
    308,
    309,
    310,
    311,
    312,
    313,
    314,
    315,
    316,
    317,
    401,
    402,
    403,
    404,
    405,
    406,
    407,
    408,
    409,
    410,
    411,
    412,
    413,
    414,
]
day_list = [1, 2, 3]
updown_list = [0, 1]
# create a list from 5 to 24
hour_list = [i for i in range(5, 25)]


# function to convert hour to stime and etime
def convert_hour_to_stime_etime(hour):
    stime = str(hour).zfill(2) + "00"
    etime = str(hour + 1).zfill(2) + "00"
    return stime, etime


def request_api(url, params):
    # make a request to the API, create backoff strategy and retry
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    response = session.get(url, params=params)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        exit()
    return response


def parse_response(response, t):
    # example data
    """
    <response>
      <header>
        <resultCode>00</resultCode>
        <resultMsg>NORMAL SERVICE.</resultMsg>
      </header>
      <body>
        <scode>101</scode>
        <line>1</line>
        <sname>신평</sname>
        <engname>Sinpyeong</engname>
        <item>
          <trainno>1135</trainno>
          <hour>13</hour>
          <time>03</time>
          <day>1</day>
          <updown>0</updown>
          <endcode>95</endcode>
        </item>
      </body>
      <numOfRows>1</numOfRows>
      <pageNo>1</pageNo>
      <totalCount>1</totalCount>
    </response>
    """

    # Parse the XML response
    root = etree.fromstring(response.content)

    # return nothing if response resultCode is not 00
    result_code = root.find(".//resultCode").text
    if result_code != "00":
        t.write(f"Error: {result_code} (Iteration: {t.n})")
        return None

    # Extract all the data inside body
    body = root.find(".//body")
    scode = body.find("scode").text
    line = body.find("line").text
    sname = body.find("sname").text
    engname = body.find("engname").text
    items = body.findall("item")
    schedules = []
    for item in items:
        trainno = item.find("trainno").text
        hour = item.find("hour").text
        time = item.find("time").text
        day = item.find("day").text
        updown = item.find("updown").text
        endcode = item.find("endcode").text

        # collect all the data in a dictionary
        data = {}
        data["scode"] = scode
        data["line"] = line
        data["sname"] = sname
        data["engname"] = engname
        data["trainno"] = trainno
        data["hour"] = hour
        data["time"] = time
        data["day"] = day
        data["updown"] = updown
        data["endcode"] = endcode

        schedules.append(data)

    return schedules


def write_to_csv(schedules):
    # write the data to a csv file
    with open("timetable.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # write the header if file is empty
        if f.tell() == 0:
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
        # write the data
        for schedule in schedules:
            writer.writerow(
                [
                    schedule["scode"],
                    schedule["line"],
                    schedule["sname"],
                    schedule["engname"],
                    schedule["trainno"],
                    schedule["hour"],
                    schedule["time"],
                    schedule["day"],
                    schedule["updown"],
                    schedule["endcode"],
                ]
            )


# exclude some scode from scode_list to resume
# scode_list = [i for i in scode_list if i > 121]

# create a progress bar
total = len(scode_list) * len(day_list) * len(updown_list) * len(hour_list)
t = tqdm(total=total, desc="Processing", unit="item")

# Loop through all combinations of scode, day, updown, and hour
for scode in scode_list:
    for day in day_list:
        for updown in updown_list:
            for hour in hour_list:
                stime, etime = convert_hour_to_stime_etime(hour)
                # make a request to the API
                params = {
                    "serviceKey": service_key,
                    "day": str(day),
                    "updown": str(updown),
                    "stime": stime,
                    "etime": etime,
                    "enum": "50",
                    "act": "xml",
                    "scode": str(scode),
                    "numOfRows": "100",
                }
                response = request_api(url, params)
                schedules = parse_response(response, t)
                if schedules:
                    write_to_csv(schedules)

                # update the progress bar
                t.update(1)
                t.refresh()
