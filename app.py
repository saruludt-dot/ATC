import streamlit as st
import pandas as pd
import base64
import streamlit.components.v1 as components

# ================= SESSION FIX =================
if "calculated" not in st.session_state:
    st.session_state["calculated"] = False

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
# 📊 STRIKES SOLD (FIXED SEEK ONLY)
# =====================================================
if page == "📊 Strikes Sold":

    st.markdown("<h1>📈 Strikes Sold Today</h1><hr>", unsafe_allow_html=True)

    expiry = st.date_input("📅 Select Expiry Date")
    expiry_str = expiry.strftime("%d-%b-%Y")

    prev_file = st.file_uploader("Upload Previous Day File", type=["csv"])
    mw_file = st.file_uploader("Upload Today MW File", type=["csv"])

    if prev_file is None or mw_file is None:
        st.info("Please upload both files")
        st.stop()

    prev_file.seek(0)
    df_prev = pd.read_csv(prev_file, on_bad_lines='skip', engine='python')

    df_prev.columns = df_prev.columns.str.strip()
    df_prev["Expiry Date"] = df_prev["Expiry Date"].astype(str).str.strip()
    df_prev = df_prev[df_prev["Expiry Date"] == expiry_str]

    df_prev["Strike Price"] = df_prev["Strike Price"].astype(str).str.replace(",", "").astype(float)
    df_prev["Close Price"] = pd.to_numeric(df_prev["Close Price"], errors="coerce")
    df_prev["Option Type"] = df_prev["Option Type"].str.strip().str.upper()

    mw_file.seek(0)
    df_mw = pd.read_csv(mw_file)

    df_mw.columns = df_mw.columns.str.strip().str.upper()

    expiry_col = next((col for col in df_mw.columns if "EXPIRY" in col), None)

    if expiry_col is None:
        st.error("❌ Expiry column not found")
        st.stop()

    df_mw[expiry_col] = pd.to_datetime(df_mw[expiry_col], errors="coerce")
    selected_expiry = pd.to_datetime(expiry)

    df_mw = df_mw[df_mw[expiry_col] == selected_expiry]

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

    st.dataframe(pd.DataFrame(results))

# =====================================================
# 📈 CALCULATIONS (ORIGINAL LOGIC RESTORED)
# =====================================================
elif page == "📈 Calculations":

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📥 Input", "📊 16 Rules", "📊 Average Only",
        "🔄 See-Saw", "📊 Variations", "⚡ Gap Adjust"
    ])

    with tab1:
        uploaded_file = st.file_uploader("Upload CSV")
        expiry = st.date_input("Expiry Date")
        strike = st.number_input("Strike", step=50)

        calculate = st.button("🚀 Calculate")

        if calculate:
            st.session_state["calculated"] = True
            st.session_state["file"] = uploaded_file
            st.session_state["expiry"] = expiry
            st.session_state["strike"] = strike

    uploaded_file = st.session_state.get("file")
    expiry = st.session_state.get("expiry")
    strike = st.session_state.get("strike")

    if uploaded_file and st.session_state["calculated"]:

        uploaded_file.seek(0)
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

        strikes = sorted(df["Strike Price"].unique())

        # -------- SEE-SAW --------
        with tab4:
            mapping = []
            for s in strikes:
                ce = get_price("CE", s-100)
                pe = get_price("PE", s+100)
                if ce and pe:
                    mapping.append([s, ce, pe])

            mapping_df = pd.DataFrame(mapping, columns=["Strike","Call","Put"])
            st.dataframe(mapping_df)

            call_list = []
            put_list = []

            for _, row in mapping_df.iterrows():
                call_list.append(f"{int(row['Strike'])},{row['Put']}")
                put_list.append(f"{int(row['Strike'])},{row['Call']}")

            call_string = "[" + ",".join(call_list) + "]"
            put_string = "[" + ",".join(put_list) + "]"

            st.session_state["call_data"] = call_string
            st.session_state["put_data"] = put_string

            st.text_area("CALL", call_string)
            st.text_area("PUT", put_string)

        # -------- GAP --------
        with tab6:

            call_input = st.session_state.get("call_data")
            put_input = st.session_state.get("put_data")

            if not call_input:
                st.warning("Run See-Saw first")
                st.stop()

            points = st.number_input("Points", value=100)
            gap = st.radio("Market", ["Gap Up","Gap Down"])

            def adj(data, change):
                items = data.replace("[","").replace("]","").split(",")
                res=[]
                for i in range(0,len(items),2):
                    try:
                        res.append(str(int(float(items[i])+change)))
                        res.append(items[i+1])
                    except: pass
                return "[" + ",".join(res) + "]"

            if st.button("Adjust"):
                if gap=="Gap Up":
                    st.code(adj(call_input,points))
                    st.code(adj(put_input,-points))
                else:
                    st.code(adj(call_input,-points))
                    st.code(adj(put_input,points))
