# app.py
# -*- coding: utf-8 -*-

import os
import math
import requests
import pandas as pd
import streamlit as st
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# =========================
# 0) 基本設定
# =========================
st.set_page_config(
    page_title="CWA 農業氣象預報儀表板",
    page_icon="🌦️",
    layout="wide",
)

# ---------- 版面美化 CSS ----------
st.markdown(
    """
    <style>
      .stApp {
        background: #e6edf5;
      }
      /* 主容器半透明卡片感 */
      .block-container {
        padding-top: 1.3rem;
        padding-bottom: 2rem;
      }
      .glass {
        background: rgba(255,255,255,0.92);
        border: 1px solid #dbeafe;
        box-shadow: 0 8px 20px rgba(15,23,42,0.12);
        border-radius: 14px;
        padding: 0.9rem 1rem;
      }
      /* 標題字 */
      h1, h2, h3, h4, h5, h6, p, label, div {
        color: #0f172a !important;
      }
      /* sidebar */
      section[data-testid="stSidebar"] {
        background: #0f172a;
        color: #e5e7eb;
      }
      section[data-testid="stSidebar"] * {
        color: #e5e7eb !important;
      }
      /* 按鈕 */
      div.stButton > button {
        background: linear-gradient(90deg, #0ea5e9 0%, #2563eb 100%);
        color: #f8fafc !important;
        border: 0px;
        border-radius: 10px;
        padding: 0.55rem 0.9rem;
        font-weight: 700;
        box-shadow: 0 6px 14px rgba(37,99,235,0.28);
        transition: transform .08s ease-in-out;
      }
      div.stButton > button:hover {
        transform: translateY(-1px);
      }
      /* 多選、下拉、日期 */
      .stSelectbox, .stMultiSelect, .stDateInput, .stSlider {
        background: rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
      }
      /* Plotly 圖卡陰影 */
      .js-plotly-plot, .stPlotlyChart {
        background: rgba(255,255,255,0.94) !important;
        border-radius: 12px !important;
        padding: 0.4rem !important;
      }
      /* dataframes */
      [data-testid="stDataFrame"] {
        background: rgba(255,255,255,0.94);
        border-radius: 12px;
        padding: 0.2rem;
      }
      /* KPI 淡化邊框、字體小一點 */
      .kpi-card {
        background: transparent;
        padding: 0.2rem 0.1rem;
      }
      .kpi-title {
        font-size: 0.95rem;
        margin: 0;
        color: #0f172a !important;
      }
      .kpi-value {
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0.15rem 0 0;
        color: #0f172a !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="glass">
      <h1 style="margin:0">🌦️ CWA 農業氣象預報：台灣地圖 + 7 天趨勢</h1>
      <p style="margin:0.35rem 0 0 0;">
        地圖標示各地每日天氣、最高/最低溫；並提供 7 天折線與單一地點溫度區間圖。
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# 1) 你的 API KEY
# =========================
# 你也可以改用環境變數：setx CWA_API_KEY "你的授權碼"
API_KEY = os.getenv("CWA_API_KEY", "CWA-544CF458-F510-49F6-B385-58CC9964DBAA")
DATASET = "F-A0010-001"
# F-A0010-001 是「檔案型」資料，必須走 fileapi + downloadType=WEB
API_URL = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/{DATASET}"

# =========================
# 2) 工具：天氣圖示（emoji）與資料解析
# =========================
def weather_emoji(weather_id) -> str:
    """
    用 Wx 的 weatherid 粗略映射 emoji（不追求 100% 對照，目標是「圖示輔助」）
    """
    try:
        wid = int(str(weather_id).strip())
    except Exception:
        return "❓"

    # 這裡採「大類」策略：晴、多雲、陰、雨、雷雨、霧
    # 若你的 weatherid 有特定規則，可再加細分。
    if wid in (1,):
        return "☀️"
    if wid in (2, 3, 4):
        return "🌤️"
    if wid in (5, 6, 7):
        return "☁️"
    if wid in (8, 9, 10, 11):
        return "🌦️"
    if wid in (12, 13, 14, 15, 16, 17, 18):
        return "🌧️"
    if wid in (19, 20, 21, 22, 23):
        return "⛈️"
    if wid in (24, 25, 26, 27, 28):
        return "🌫️"
    # 其他
    return "🌈"


def pick_numeric_value(daily_item: dict):
    """
    daily_item 通常至少有 dataDate，其他欄位可能叫 temperature / maxT / minT / value...
    這裡用「找得到就抓」的方式，回傳第一個能轉 float 的欄位值。
    """
    if not isinstance(daily_item, dict):
        return None
    for k, v in daily_item.items():
        if k == "dataDate":
            continue
        # 排除明顯文字欄位
        if isinstance(v, (dict, list)):
            continue
        try:
            fv = float(str(v).strip())
            if math.isfinite(fv):
                return fv
        except Exception:
            continue
    return None


@st.cache_data(ttl=600, show_spinner=False)
def fetch_and_parse(api_key: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    回傳：
      - df_wx: locationName, dataDate, weather, weatherid, emoji
      - df_temp: locationName, dataDate, MaxT, MinT
    """
    params = {"Authorization": api_key, "format": "JSON", "downloadType": "WEB"}
    r = requests.get(API_URL, params=params, timeout=30)
    r.raise_for_status()
    raw = r.json()

    # 你的實際結構是：data['cwaopendata']['resources']['resource']['data']['agrWeatherForecasts']['weatherForecasts']['location']
    locs = (
        raw["cwaopendata"]["resources"]["resource"]["data"]
        ["agrWeatherForecasts"]["weatherForecasts"]["location"]
    )

    # Wx
    wx_rows = []
    # 溫度
    temp_rows = []

    for loc in locs:
        name = loc.get("locationName")
        we = loc.get("weatherElements", {})

        # Wx
        wx_daily = we.get("Wx", {}).get("daily", [])
        for d in wx_daily:
            dt = pd.to_datetime(d.get("dataDate"), errors="coerce")
            wid = d.get("weatherid")
            wx_rows.append({
                "locationName": name,
                "dataDate": dt,
                "weather": d.get("weather"),
                "weatherid": wid,
                "emoji": weather_emoji(wid),
            })

        # MaxT / MinT（各自 daily list）
        max_daily = we.get("MaxT", {}).get("daily", [])
        min_daily = we.get("MinT", {}).get("daily", [])

        # 先轉成 dict：date -> value
        max_map = {}
        for d in max_daily:
            dt = pd.to_datetime(d.get("dataDate"), errors="coerce")
            max_map[dt] = pick_numeric_value(d)

        min_map = {}
        for d in min_daily:
            dt = pd.to_datetime(d.get("dataDate"), errors="coerce")
            min_map[dt] = pick_numeric_value(d)

        # 用 wx_daily 的日期當主鍵（通常 7 天齊全）
        dates = sorted(set([pd.to_datetime(x.get("dataDate"), errors="coerce") for x in wx_daily]))
        for dt in dates:
            temp_rows.append({
                "locationName": name,
                "dataDate": dt,
                "MaxT": max_map.get(dt),
                "MinT": min_map.get(dt),
            })

    df_wx = pd.DataFrame(wx_rows).dropna(subset=["dataDate"])
    df_temp = pd.DataFrame(temp_rows).dropna(subset=["dataDate"])

    # 去除重複
    df_wx = df_wx.drop_duplicates(subset=["locationName", "dataDate"])
    df_temp = df_temp.drop_duplicates(subset=["locationName", "dataDate"])

    return df_wx, df_temp


# =========================
# 3) 台灣地圖：地點座標（可自行加/改）
# =========================
# 你的資料目前 location count = 6，實際名稱以 df_wx['locationName'] 為準。
# 如果遇到不在 dict 的地點，地圖會跳過那個點（其他圖表不受影響）。
TAIWAN_COORDS = {
    # 常見縣市（你可以依 df_wx 的 locationName 來補）
    "臺北市": (25.0375, 121.5637),
    "新北市": (25.0120, 121.4657),
    "桃園市": (24.9937, 121.3010),
    "臺中市": (24.1477, 120.6736),
    "臺南市": (22.9999, 120.2270),
    "高雄市": (22.6273, 120.3014),
    "基隆市": (25.1276, 121.7392),
    "新竹市": (24.8138, 120.9675),
    "嘉義市": (23.4801, 120.4491),

    # 也可能是「區域型」命名（農業預報有時用北/中/南/東/離島）
    "北部": (25.0478, 121.5319),
    "中部": (23.9739, 120.9820),
    "南部": (22.9999, 120.2270),
    "東部": (23.9911, 121.6016),
    "離島": (24.4317, 118.3186),  # 金門附近
    "澎湖": (23.5712, 119.5794),
    "金門": (24.4371, 118.3186),
    "馬祖": (26.1600, 119.9497),
    "花蓮": (23.9872, 121.6016),
    "臺東": (22.7583, 121.1444),
    # 農業預報常用的區域型名稱
    "北部地區": (25.05, 121.53),
    "中部地區": (24.15, 120.67),
    "南部地區": (22.99, 120.21),
    "東北部地區": (24.77, 121.75),
    "東部地區": (23.99, 121.60),
    "東南部地區": (22.76, 121.15),
}


def add_coords(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["lat"] = df["locationName"].map(lambda x: TAIWAN_COORDS.get(x, (None, None))[0])
    df["lon"] = df["locationName"].map(lambda x: TAIWAN_COORDS.get(x, (None, None))[1])
    return df


# =========================
# 4) Sidebar：控制項
# =========================
with st.sidebar:
    st.markdown("## ⚙️ 控制面板")
    api_ok = API_KEY and API_KEY != "YOUR_KEY"

    st.markdown("**資料來源：CWA OpenData（F-A0010-001）**")
    if not api_ok:
        st.warning("請先把 API_KEY 改成你的授權碼（或設定環境變數 CWA_API_KEY）")

    refresh = st.button("🔄 重新抓取資料")

# 如果按 refresh：清 cache
if refresh:
    fetch_and_parse.clear()

# =========================
# 5) 抓資料 + 合併
# =========================
try:
    df_wx, df_temp = fetch_and_parse(API_KEY)
except Exception as e:
    st.error(f"抓取/解析失敗：{e}")
    st.stop()

# 合併（同 location + date）
df = pd.merge(
    df_wx,
    df_temp,
    on=["locationName", "dataDate"],
    how="left",
)

df = df.sort_values(["locationName", "dataDate"])

locations = sorted(df["locationName"].dropna().unique().tolist())
dates = sorted(df["dataDate"].dropna().dt.date.unique().tolist())

with st.sidebar:
    st.markdown("---")
    sel_date = st.selectbox("📅 地圖顯示日期", dates, index=0 if dates else 0)
    compare_locs = st.multiselect("🧭 折線圖地點（可多選）", locations, default=locations[: min(4, len(locations))])

# =========================
# 6) 上方 KPI 卡片
# =========================
today_df = df[df["dataDate"].dt.date == sel_date].copy()
colA, colB, colC = st.columns(3)

def kpi_card(col, title, value, icon):
    col.markdown(
        f"""
        <div class="kpi-card">
          <p class="kpi-title">{icon} {title}</p>
          <p class="kpi-value">{value}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

kpi_card(colA, "地點數", f"{len(locations)}", "🗺️")
kpi_card(colB, "日期範圍", f"{min(dates)} → {max(dates)}" if dates else "—", "📆")
kpi_card(colC, "地圖日期", f"{sel_date}", "📍")

st.markdown("")

# =========================
# 7) 台灣地圖：標示各地資料（含 emoji/溫度）
# =========================
left, right = st.columns([1, 1])

with left:
    st.markdown(
        """
        <div class="glass">
          <h2 style="margin:0">🗺️ 台灣地圖：各地每日概況</h2>
          <p style="margin:0.4rem 0 0 0;">
            依選定日期標示各地天氣圖示、最高/最低溫（若該地點座標未設定，會暫時跳過地圖點）。
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    map_df = add_coords(today_df)
    map_df = map_df.dropna(subset=["lat", "lon"]).copy()

    if map_df.empty:
        st.warning("⚠️ 目前沒有可用座標的地點可畫在地圖上。請把 locationName 對應到 TAIWAN_COORDS 補上座標。")
    else:
        # tooltip 文字
        map_df["tooltip"] = map_df.apply(
            lambda r: f"{r['emoji']} {r['locationName']} ({r['dataDate'].date()})\n"
                      f"天氣：{r.get('weather','')}\n"
                      f"MaxT：{r.get('MaxT','—')}°C  MinT：{r.get('MinT','—')}°C",
            axis=1
        )
        map_df["tooltip_html"] = map_df.apply(
            lambda r: f"<div style='color:#0f172a; font-weight:600;'>{r['emoji']} {r['locationName']} ({r['dataDate'].date()})</div>"
                      f"<div style='color:#0f172a;'>天氣：{r.get('weather','')}</div>"
                      f"<div style='color:#0f172a;'>MaxT：{r.get('MaxT','—')}°C　MinT：{r.get('MinT','—')}°C</div>",
            axis=1
        )

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position="[lon, lat]",
            get_radius=15000,
            pickable=True,
            auto_highlight=True,
            get_fill_color="[37, 99, 235, 220]",
            get_line_color="[255, 255, 255, 220]",
            line_width_min_pixels=1,
        )

        # 地圖中心點：台灣
        view_state = pdk.ViewState(
            latitude=23.7,
            longitude=121.0,
            zoom=6.5,
            pitch=0,
        )

        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "html": "{tooltip_html}",
                "style": {
                    "backgroundColor": "#ffffff",
                    "color": "#0f172a",
                    "fontSize": "14px",
                    "border": "1px solid #0f172a"
                },
            },
            map_style=None,  # 不用 Mapbox key
        )

        st.pydeck_chart(deck, use_container_width=True, height=650)

with right:
    st.markdown(
        """
        <div class="glass">
          <h2 style="margin:0">📋 今日資料（含圖示）</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    show_cols = ["emoji", "locationName", "dataDate", "weather", "MaxT", "MinT"]
    st.dataframe(
        today_df[show_cols].sort_values("locationName"),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("")

# =========================
# 8) 7 天最高/最低溫折線圖（多地點）
# =========================
st.markdown(
    """
    <div class="glass">
      <h2 style="margin:0">📈 7 天最高/最低溫折線圖（可多地點比較）</h2>
      <p style="margin:0.4rem 0 0 0;">
        你可以在左側選多個地點進行比較。
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

cmp_df = df[df["locationName"].isin(compare_locs)].copy()

# 轉長表做 Plotly
long_df = pd.melt(
    cmp_df,
    id_vars=["locationName", "dataDate"],
    value_vars=["MaxT", "MinT"],
    var_name="TempType",
    value_name="TempC",
)

fig_lines = px.line(
    long_df.dropna(subset=["TempC"]),
    x="dataDate",
    y="TempC",
    color="locationName",
    line_dash="TempType",
    markers=True,
    title="",
)
fig_lines.update_layout(
    height=420,
    margin=dict(l=10, r=10, t=20, b=10),
    legend_title_text="地點（線型：MaxT/MinT）",
)
st.plotly_chart(fig_lines, use_container_width=True)

st.markdown("")

# =========================
# 9) 小提醒：座標補齊
# =========================
missing = sorted(set(locations) - set(TAIWAN_COORDS.keys()))
if missing:
    st.info(
        "🧩 地圖缺少座標的地點（不影響圖表）：\n\n- "
        + "\n- ".join(missing)
        + "\n\n你可以到程式裡的 `TAIWAN_COORDS` 字典把它們補上 (lat, lon)。"
    )

st.markdown(
    """
    <div class="glass">
      <p style="margin:0;">
        ✅ 提示：若要把授權碼藏起來，建議改用環境變數 <code>CWA_API_KEY</code>。
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
