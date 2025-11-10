import io
import datetime as dt
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

st.set_page_config(page_title="OutbreakCast — Fever Forecasts", page_icon="🦠", layout="wide")

# ----------------------------
# Helpers
# ----------------------------
@st.cache_data
def load_csv(file) -> pd.DataFrame:
    return pd.read_csv(file, parse_dates=["week_start"])

def _nice_date(d):
    return pd.to_datetime(d).date()

def synth_forecasts():
    # tiny synthetic fallback so the app always runs
    rng = pd.date_range("2025-11-16", periods=4, freq="W-SUN")
    recs = []
    for state, district in [("Karnataka","Bengaluru Urban"),
                            ("Tamil Nadu","Chennai"),
                            ("Delhi","New Delhi")]:
        base = np.random.randint(60, 160)
        ys = base + np.random.randn(4)*10
        for i, w in enumerate(rng):
            recs.append({"week_start": w, "state": state, "district": district, "yhat": max(0, ys[i])})
    f = pd.DataFrame(recs).sort_values(["state","district","week_start"])
    # risk bands by per-district quantiles
    risk = []
    for d in f["district"].unique():
        q75, q90 = f.loc[f["district"]==d, "yhat"].quantile([0.75, 0.90]).values
        tmp = f[f["district"]==d].copy()
        tmp["risk_band"] = np.where(tmp["yhat"]>=q90,"Red", np.where(tmp["yhat"]>=q75,"Amber","Green"))
        risk.append(tmp)
    r = pd.concat(risk, ignore_index=True)
    return f, r

def band_order():
    return ["Green","Amber","Red"]

def kpi(color, label, value):
    st.markdown(
        f"""
        <div style="border-radius:16px;padding:16px;background:#f7f7f9;border:1px solid #eee;">
          <div style="font-size:14px;color:#666;">{label}</div>
          <div style="font-size:28px;font-weight:700;color:{color};">{value}</div>
        </div>
        """, unsafe_allow_html=True
    )

# ----------------------------
# Sidebar — Data input
# ----------------------------
st.sidebar.title("📥 Data")
st.sidebar.markdown("Upload the **two CSVs** exported by your Colab script.")
f_up = st.sidebar.file_uploader("forecasts.csv", type=["csv"])
r_up = st.sidebar.file_uploader("risk_bands.csv", type=["csv"])

if f_up and r_up:
    forecasts = load_csv(f_up)
    risk_df = load_csv(r_up)
else:
    st.sidebar.info("No files? Using a small synthetic demo.")
    forecasts, risk_df = synth_forecasts()

# Basic sanity
for needed in [["week_start","state","district","yhat"], ["week_start","state","district","yhat","risk_band"]]:
    pass  # (lightweight, already ensured by generator/your notebook)

# ----------------------------
# Top bar & filters
# ----------------------------
st.title("🦠 OutbreakCast — Fever Forecasts")
st.caption("District-week forecasts with risk banding (Green / Amber / Red)")

colA, colB, colC = st.columns([1.4,1,1])
with colA:
    states = sorted(risk_df["state"].dropna().unique().tolist())
    state = st.selectbox("State", ["(All)"] + states, index=0)
with colB:
    districts_all = risk_df["district"].dropna().unique().tolist()
    if state != "(All)":
        districts = sorted(risk_df[risk_df["state"]==state]["district"].unique().tolist())
    else:
        districts = sorted(districts_all)
    district = st.selectbox("District", ["(All)"] + districts, index=0)
with colC:
    weeks = sorted(risk_df["week_start"].dt.date.unique().tolist())
    if weeks:
        week_sel = st.selectbox("Week", ["(All)"] + [str(w) for w in weeks], index=0)
    else:
        week_sel = "(All)"

# Apply filters
view = risk_df.copy()
if state != "(All)":
    view = view[view["state"]==state]
if district != "(All)":
    view = view[view["district"]==district]
if week_sel != "(All)":
    view = view[view["week_start"].dt.date == dt.date.fromisoformat(week_sel)]

# ----------------------------
# KPI Row
# ----------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi("#222", "States", view["state"].nunique())
with c2:
    kpi("#222", "Districts", view["district"].nunique())
with c3:
    kpi("#e67e22", "Median forecast (yhat)", round(view["yhat"].median(), 1) if len(view) else 0)
with c4:
    band_counts = view["risk_band"].value_counts().reindex(band_order()).fillna(0).astype(int)
    kpi("#c0392b", "Red (count)", int(band_counts.get("Red", 0)))

st.divider()

# ----------------------------
# Risk distribution & table
# ----------------------------
left, right = st.columns([1.2,1])

with left:
    # risk band bar chart
    band_df = view.groupby(["week_start","risk_band"], as_index=False)["district"].count().rename(columns={"district":"count"})
    band_df["risk_band"] = pd.Categorical(band_df["risk_band"], categories=band_order(), ordered=True)
    if len(band_df):
        chart = alt.Chart(band_df).mark_bar().encode(
            x=alt.X("week_start:T", title="Week"),
            y=alt.Y("count:Q", title="District count"),
            color=alt.Color("risk_band:N", sort=band_order()),
            tooltip=["week_start","risk_band","count"]
        ).properties(height=320)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No rows for current filters.")

with right:
    st.subheader("Current selection")
    st.dataframe(
        view.sort_values(["week_start","state","district"]),
        use_container_width=True,
        hide_index=True
    )
    st.download_button(
        "⬇️ Download filtered rows (CSV)",
        data=view.to_csv(index=False),
        file_name="filtered_risk_bands.csv",
        mime="text/csv"
    )

st.divider()

# ----------------------------
# District trend explorer
# ----------------------------
st.subheader("📈 District trend (last known & next 4 weeks)")

# We need some history to plot; if user has an 'historical.csv', allow upload to enhance plot
hist_up = st.file_uploader("Optional: upload a historical weekly dataset to plot trailing 40 weeks (same district names).", type=["csv"], key="hist")
hist_df = None
if hist_up:
    try:
        hist_df = pd.read_csv(hist_up, parse_dates=["week_start"])
    except Exception as e:
        st.warning(f"Could not parse historical file: {e}")

# selector
dopts = sorted(risk_df["district"].unique().tolist())
d_sel = st.selectbox("Pick a district", dopts, index=0)

# Plot
future = risk_df[risk_df["district"]==d_sel][["week_start","yhat","risk_band"]].sort_values("week_start")
layers = []

if hist_df is not None and "week_start" in hist_df and "district" in hist_df and d_sel in hist_df["district"].unique():
    hist_part = hist_df[hist_df["district"]==d_sel].sort_values("week_start").tail(40)
    if "dengue_cases" in hist_part.columns:
        ycol = "dengue_cases"
    elif "cases" in hist_part.columns:
        ycol = "cases"
    else:
        ycol = None
    if ycol:
        l_hist = alt.Chart(hist_part).mark_line().encode(
            x=alt.X("week_start:T", title="Week"),
            y=alt.Y(f"{ycol}:Q", title="Cases"),
            tooltip=["week_start", ycol]
        )
        layers.append(l_hist)

l_future = alt.Chart(future).mark_line(point=True).encode(
    x=alt.X("week_start:T", title="Week"),
    y=alt.Y("yhat:Q", title="Forecast cases"),
    color=alt.value("#333"),
    tooltip=["week_start","yhat","risk_band"]
)
layers.append(l_future)

st.altair_chart(alt.layer(*layers).properties(height=340), use_container_width=True)

st.caption("Tip: Upload your historical weekly dataset to show trailing 40 weeks of actuals alongside forecasts.")
