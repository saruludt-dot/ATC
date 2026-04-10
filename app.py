import streamlit as st
import pandas as pd
import base64
import streamlit.components.v1 as components

# ---------------- SESSION STATE ----------------
if "calculated" not in st.session_state:
    st.session_state.calculated = False

if "atm_strike" not in st.session_state:
    st.session_state.atm_strike = None

# ---------------- IMAGE ----------------
def get_img(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo = get_img("logo.png")

st.sidebar.markdown(
    f"<img src='data:image/png;base64,{logo}' width='100%'>",
    unsafe_allow_html=True
)

st.sidebar.markdown("### 📌 Navigation")
page = st.sidebar.radio("", ["📈 Calculations", "📊 Strikes Sold"])

# =====================================================
# 📊 STRIKES SOLD
# =====================================================
if page == "📊 Strikes Sold":

    st.title("📈 Strikes Sold Today")

    prev_file = st.file_uploader("Upload Previous Day File", type=["csv"])
    mw_file = st.file_uploader("Upload Today MW File", type=["csv"])

    if prev_file is None or mw_file is None:
        st.info("Please upload both files")
        st.stop()

    df_prev = pd.read_csv(prev_file, on_bad_lines='skip', engine='python')
    df_prev.columns = df_prev.columns.str.strip()

    df_prev["Strike Price"] = df_prev["Strike Price"].astype(str).str.replace(",", "").astype(float)
    df_prev["Close Price"] = pd.to_numeric(df_prev["Close Price"], errors="coerce")
    df_prev["Option Type"] = df_prev["Option Type"].str.strip().str.upper()

    df_mw = pd.read_csv(mw_file)
    df_mw.columns = df_mw.columns.str.strip().str.upper()

    df_mw["STRIKE"] = df_mw["STRIKE"].astype(str).str.replace(",", "").astype(float)
    df_mw["LOW"] = pd.to_numeric(df_mw["LOW"], errors="coerce")
    df_mw["HIGH"] = pd.to_numeric(df_mw["HIGH"], errors="coerce")

    df_mw["OPTION TYPE"] = df_mw["OPTION TYPE"].replace({
        "Call": "CE", "Put": "PE", "CALL": "CE", "PUT": "PE"
    })

    df_mw = df_mw[df_mw["SYMBOL"] == "NIFTY"]

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

        ce = df_mw[(df_mw["OPTION TYPE"] == "CE") & (abs(df_mw["STRIKE"] - strike) < 1)]
        pe = df_mw[(df_mw["OPTION TYPE"] == "PE") & (abs(df_mw["STRIKE"] - strike) < 1)]

        ce_status = "❌ Not Sold"
        pe_status = "❌ Not Sold"

        if not ce.empty:
            if ce.iloc[0]["LOW"] <= value <= ce.iloc[0]["HIGH"]:
                ce_status = "✅ Sold"

        if not pe.empty:
            if pe.iloc[0]["LOW"] <= value <= pe.iloc[0]["HIGH"]:
                pe_status = "✅ Sold"

        results.append({
            "Strike": strike,
            "Average": round(value, 2),
            "CE Status": ce_status,
            "PE Status": pe_status
        })

    result_df = pd.DataFrame(results).sort_values(by="Strike")
    st.dataframe(result_df, use_container_width=True)

# =====================================================
# 📈 CALCULATIONS
# =====================================================
elif page == "📈 Calculations":

    st.title("📊 Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        uploaded_file = st.file_uploader("📥 Upload CSV")

    with col2:
        expiry = st.date_input("📅 Expiry Date")

    with col3:
        strike = st.number_input("🎯 Strike", step=50)

    if st.button("🚀 Calculate", use_container_width=True):
        st.session_state.calculated = True

    if uploaded_file and st.session_state.calculated:

        df = pd.read_csv(uploaded_file, on_bad_lines='skip', engine='python')
        df.columns = df.columns.str.strip()

        df["Expiry Date"] = df["Expiry Date"].astype(str).str.strip()
        df["Option Type"] = df["Option Type"].str.strip().str.upper()
        df["Strike Price"] = df["Strike Price"].astype(str).str.replace(",", "").astype(float)

        df["Close Price"] = pd.to_numeric(df["Close Price"], errors="coerce")

        expiry_str = expiry.strftime("%d-%b-%Y")

        def get_price(opt, s):
            r = df[(df["Expiry Date"] == expiry_str) &
                   (df["Option Type"] == opt) &
                   (df["Strike Price"] == s)]
            return r.iloc[0]["Close Price"] if not r.empty else None

        diff_list = []
        strikes = df[df["Expiry Date"] == expiry_str]["Strike Price"].unique()

        for s in strikes:
            ce = get_price("CE", s)
            pe = get_price("PE", s)

            if ce and pe:
                diff_list.append((s, abs(ce - pe)))

        if diff_list:
            atm_strike = min(diff_list, key=lambda x: x[1])[0]
            st.session_state.atm_strike = atm_strike

        if st.session_state.atm_strike:

            tab1, tab2 = st.tabs(["📊 Average", "📍 ATM"])

            with tab1:
                rows = []
                for s in sorted(strikes):
                    ce = get_price("CE", s)
                    pe = get_price("PE", s)
                    if ce and pe:
                        rows.append([int(s), round((ce + pe) / 2, 2)])

                df_out = pd.DataFrame(rows, columns=["Strike", "Average"])
                st.dataframe(df_out, use_container_width=True)

            with tab2:
                st.success(f"ATM Strike: {int(st.session_state.atm_strike)}")

    if st.button("🔄 Reset"):
        st.session_state.calculated = False
        st.session_state.atm_strike = None
