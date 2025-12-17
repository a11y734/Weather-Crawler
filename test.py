import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
from pprint import pprint

API_KEY = os.getenv("CWA_API_KEY", "CWA-544CF458-F510-49F6-B385-58CC9964DBAA").strip()
if not API_KEY:
    raise ValueError("請把實際金鑰設在環境變數 CWA_API_KEY。")

# F-A0010-001 屬於檔案型資料，要走 fileapi 而不是 rest/datastore
DATASET_ID = "F-A0010-001"
url = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/{DATASET_ID}"

params = {
    "Authorization": API_KEY,
    "downloadType": "WEB",
    "format": "JSON"
}

r = requests.get(url, params=params, timeout=30)
if r.status_code != 200:
    print(f"API 回應錯誤狀態碼 {r.status_code}")
    print(r.text)
    r.raise_for_status()

data = r.json()

print("API OK")


print("data type:", type(data))
print("data keys:")
pprint(list(data.keys()))

op = data["cwaopendata"]

print("cwaopendata type:", type(op))
print("cwaopendata keys:")
pprint(list(op.keys()))

op = data["cwaopendata"]
res = op["resources"]

print("resources type:", type(res))
print("resources keys:")
pprint(list(res.keys()))

op = data["cwaopendata"]
resource = op["resources"]["resource"]

print("resource type:", type(resource))

# 如果是 list，就看第 0 筆有哪些 key
if isinstance(resource, list):
    print("resource[0] keys:")
    pprint(list(resource[0].keys()))
else:
    print("resource keys:")
    pprint(list(resource.keys()))

    resource = data["cwaopendata"]["resources"]["resource"]
d = resource["data"]

print("data type:", type(d))

if isinstance(d, dict):
    print("data keys:")
    pprint(list(d.keys()))
elif isinstance(d, list):
    print("data[0] keys:")
    pprint(list(d[0].keys()))

    
agr = data["cwaopendata"]["resources"]["resource"]["data"]["agrWeatherForecasts"]

print("agrWeatherForecasts type:", type(agr))

if isinstance(agr, dict):
    print("agrWeatherForecasts keys:")
    pprint(list(agr.keys()))
elif isinstance(agr, list):
    print("agrWeatherForecasts[0] keys:")
    pprint(list(agr[0].keys()))

wf = data["cwaopendata"]["resources"]["resource"]["data"]["agrWeatherForecasts"]["weatherForecasts"]

print("weatherForecasts type:", type(wf))

if isinstance(wf, dict):
    print("weatherForecasts keys:")
    pprint(list(wf.keys()))
elif isinstance(wf, list):
    print("weatherForecasts[0] keys:")
    pprint(list(wf[0].keys()))

loc = data["cwaopendata"]["resources"]["resource"]["data"]["agrWeatherForecasts"]["weatherForecasts"]["location"]

print("location type:", type(loc))

if isinstance(loc, list):
    print("location count:", len(loc))
    print("location[0] keys:")
    pprint(list(loc[0].keys()))
else:
    print("location keys:")
    pprint(list(loc.keys()))

locs = data["cwaopendata"]["resources"]["resource"]["data"]["agrWeatherForecasts"]["weatherForecasts"]["location"]

we = locs[0]["weatherElements"]
print("weatherElements type:", type(we))

if isinstance(we, list):
    print("weatherElements count:", len(we))
    print("weatherElements[0] keys:")
    pprint(list(we[0].keys()))
else:
    print("weatherElements keys:")
    pprint(list(we.keys()))

locs = data["cwaopendata"]["resources"]["resource"]["data"]["agrWeatherForecasts"]["weatherForecasts"]["location"]

wx = locs[0]["weatherElements"]["Wx"]

print("Wx type:", type(wx))

if isinstance(wx, dict):
    print("Wx keys:")
    pprint(list(wx.keys()))
elif isinstance(wx, list):
    print("Wx[0] keys:")
    pprint(list(wx[0].keys()))

locs = data["cwaopendata"]["resources"]["resource"]["data"]["agrWeatherForecasts"]["weatherForecasts"]["location"]
daily = locs[0]["weatherElements"]["Wx"]["daily"]

print("daily type:", type(daily))

if isinstance(daily, list):
    print("daily count:", len(daily))
    print("daily[0] keys:")
    pprint(list(daily[0].keys()))
else:
    print("daily keys:")
    pprint(list(daily.keys()))