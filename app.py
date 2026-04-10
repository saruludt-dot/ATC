import streamlit as st
import pandas as pd
import base64
import streamlit.components.v1 as components

# ---------------- IMAGE ----------------
def get_img(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ---------------- SIDEBAR ----------------
logo = get_img("logo.png")

st.sidebar.markdown(
    f"<img src='data:image/png;base64,{logo}' width='100%'>",
    unsafe_allow_html=True
)

st.sidebar.markdown("""
<style>
section[data-testid="stSidebar"] > div { padding-top: -15px; }
section[data-testid="stSidebar"] h3 { margin-top: 0px; margin-bottom: -20px; }
div[data-testid="stRadio"] > div { gap: 5px; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 📌 Navigation")

page = st.sidebar.radio("", ["📊 Strikes Sold", "📈 Calculations"])

# =====================================================
# ✅ STRIKES SOLD (NEW LOGIC - DIRECT)
# =====================================================
if page == "📊 Strikes Sold":

    st.markdown("<h1>📈 Strikes Sold Today</h1><hr>", unsafe_allow_html=True)

    prev_file = st.file_uploader("Upload Previous Day File", type=["csv"])
    mw_file = st.file_uploader("Upload Today MW File", type=["csv"])

    if prev_file is None or mw_file is None:
        st.info("Please upload both files")
        st.stop()

    # -------- PREVIOUS DAY --------
    df_prev = pd.read_csv(prev_file, on_bad_lines='skip', engine='python')
    df_prev.columns = df_prev.columns.str.strip()

    df_prev["Strike Price"] = df_prev["Strike Price"].astype(str).str.replace(",", "").astype(float)
    df_prev["Close Price"] = pd.to_numeric(df_prev["Close Price"], errors="coerce")
    df_prev["Option Type"] = df_prev["Option Type"].str.strip().str.upper()

    # -------- MW FILE --------
    df_mw = pd.read_csv(mw_file)
    df_mw.columns = df_mw.columns.str.strip().str.upper()

    df_mw["STRIKE"] = df_mw["STRIKE"].astype(str).str.replace(",", "").astype(float)
    df_mw["LOW"] = pd.to_numeric(df_mw["LOW"], errors="coerce")
    df_mw["HIGH"] = pd.to_numeric(df_mw["HIGH"], errors="coerce")

    df_mw["OPTION TYPE"] = df_mw["OPTION TYPE"].replace({
        "Call": "CE", "Put": "PE", "CALL": "CE", "PUT": "PE"
    })

    df_mw = df_mw[df_mw["SYMBOL"] == "NIFTY"]

    # -------- PROCESS --------
    results = []

    strikes = df_prev["Strike Price"].unique()

    for strike in strikes:

        ce_row = df_prev[(df_prev["Option Type"] == "CE") & (df_prev["Strike Price"] == strike)]
        pe_row = df_prev[(df_prev["Option Type"] == "PE") & (df_prev["Strike Price"] == strike)]

        if ce_row.empty or pe_row.empty:
            continue

        ce_close = ce_row.iloc[0]["Close Price"]
        pe_close = pe_row.iloc[0]["Close Price"]

        if pd.isnull(ce_close) or pd.isnull(pe_close):
            continue

        value = (ce_close + pe_close) / 2

        # ---- CE ----
        ce = df_mw[(df_mw["OPTION TYPE"] == "CE") & (abs(df_mw["STRIKE"] - strike) < 1)]

        ce_low = ce_high = None
        ce_status = "❌ Not Sold"

        if not ce.empty:
            ce_low = ce.iloc[0]["LOW"]
            ce_high = ce.iloc[0]["HIGH"]
            if ce_low <= value <= ce_high:
                ce_status = "✅ Sold"

        # ---- PE ----
        pe = df_mw[(df_mw["OPTION TYPE"] == "PE") & (abs(df_mw["STRIKE"] - strike) < 1)]

        pe_low = pe_high = None
        pe_status = "❌ Not Sold"

        if not pe.empty:
            pe_low = pe.iloc[0]["LOW"]
            pe_high = pe.iloc[0]["HIGH"]
            if pe_low <= value <= pe_high:
                pe_status = "✅ Sold"

        # ---- S/R ----
        S2 = S1 = R1 = R2 = None

        if ce_status == "✅ Sold" and pe_status == "✅ Sold":
            S2 = strike - (2 * value)
            S1 = strike - value
            R1 = strike + value
            R2 = strike + (2 * value)

        results.append({
            "Strike": strike,
            "Average": round(value, 2),
            "CE Low": ce_low,
            "CE High": ce_high,
            "PE Low": pe_low,
            "PE High": pe_high,
            "CE Status": ce_status,
            "PE Status": pe_status,
            "S2": S2,
            "S1": S1,
            "R1": R1,
            "R2": R2
        })

    if len(results) == 0:
        st.warning("No matching data found. Check files.")
    else:
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values(by="Strike").reset_index(drop=True)
        st.dataframe(result_df, use_container_width=True)

# =====================================================
# ✅ CALCULATIONS (OLD SAFE VERSION)
# =====================================================
elif page == "📈 Calculations":

    st.markdown("<h1>📈 Dashboard</h1><hr>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📥 Upload CSV")
    expiry = st.date_input("📅 Expiry Date")
    strike = st.number_input("🎯 Strike", step=50)

    calculate = st.button("🚀 Calculate")

    if uploaded_file and calculate:

        df = pd.read_csv(uploaded_file, on_bad_lines='skip', engine='python')

        df.columns = df.columns.str.strip()
        df["Expiry Date"] = df["Expiry Date"].astype(str).str.strip()
        df["Option Type"] = df["Option Type"].str.strip().str.upper()

        df["Strike Price"] = df["Strike Price"].astype(str).str.replace(",", "").astype(float)

        df["Close Price"] = pd.to_numeric(df["Close Price"], errors="coerce")

        expiry_str = expiry.strftime("%d-%b-%Y")

        def get_price(opt, s):
            r = df[(df["Expiry Date"]==expiry_str) & (df["Option Type"]==opt) & (df["Strike Price"]==s)]
            return r.iloc[0]["Close Price"] if not r.empty else None

        rows = []

        ce = get_price("CE", strike)
        pe = get_price("PE", strike)

        if ce and pe:
            avg = (ce + pe)/2
            rows.append([strike, avg])

        result_df = pd.DataFrame(rows, columns=["Strike","Average"])
        st.dataframe(result_df)
