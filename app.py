import streamlit as st
import pandas as pd
import base64
import streamlit.components.v1 as components

# =========================
# SESSION INIT
# =========================
if "calculated" not in st.session_state:
    st.session_state["calculated"] = False

# =========================
# SAFE CSV READ
# =========================
def safe_read(file):
    if file is None:
        return None
    file.seek(0)
    return pd.read_csv(file, on_bad_lines='skip', engine='python')

# =========================
# GAP PROCESS
# =========================
def adjust_list(data, change):
    data = data.replace("[", "").replace("]", "")
    items = data.split(",")

    result = []
    for i in range(0, len(items), 2):
        try:
            strike = float(items[i])
            price = items[i+1]
            result.extend([int(strike + change), price])
        except:
            continue

    return "[" + ",".join(map(str, result)) + "]"

# =========================
# SIDEBAR
# =========================
def get_img(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo = get_img("logo.png")

st.sidebar.markdown(
    f"<img src='data:image/png;base64,{logo}' width='100%'>",
    unsafe_allow_html=True
)

page = st.sidebar.radio("", ["📈 Calculations", "📊 Strikes Sold"])

# =====================================================
# 📈 CALCULATIONS
# =====================================================
if page == "📈 Calculations":

    st.title("📈 Dashboard")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📥 Input", "📊 16 Rules", "📊 Average Only",
        "🔄 See-Saw", "📊 Variations", "⚡ Gap Adjust"
    ])

    # ---------------- INPUT ----------------
    with tab1:
        col1, col2, col3 = st.columns(3)

        with col1:
            uploaded_file = st.file_uploader("Upload CSV")

        with col2:
            expiry = st.date_input("Expiry Date")

        with col3:
            strike = st.number_input("Strike", step=50)

        calculate = st.button("🚀 Calculate", use_container_width=True)

        if calculate:
            st.session_state["calculated"] = True
            st.session_state["file"] = uploaded_file
            st.session_state["expiry"] = expiry
            st.session_state["strike"] = strike

    # LOAD FROM SESSION
    uploaded_file = st.session_state.get("file")
    expiry = st.session_state.get("expiry")
    strike = st.session_state.get("strike")

    if uploaded_file and st.session_state["calculated"]:

        df = safe_read(uploaded_file)

        df.columns = df.columns.str.strip()
        df["Expiry Date"] = df["Expiry Date"].astype(str).str.strip()
        df["Option Type"] = df["Option Type"].str.strip().str.upper()

        df["Strike Price"] = df["Strike Price"].astype(str).str.replace(",", "").astype(float)
        df["Close Price"] = pd.to_numeric(df["Close Price"], errors="coerce")
        df["High Price"] = pd.to_numeric(df["High Price"], errors="coerce")
        df["Low Price"] = pd.to_numeric(df["Low Price"], errors="coerce")

        expiry_str = expiry.strftime("%d-%b-%Y")

        def get_price(opt, s):
            r = df[(df["Expiry Date"]==expiry_str) & (df["Option Type"]==opt) & (df["Strike Price"]==s)]
            return r.iloc[0]["Close Price"] if not r.empty else None

        # =========================
        # ATM DETECTION
        # =========================
        diff_list = []
        strikes = df[df["Expiry Date"]==expiry_str]["Strike Price"].unique()

        for s in strikes:
            ce = get_price("CE", s)
            pe = get_price("PE", s)
            if ce and pe and 10 < ce < 1000 and 10 < pe < 1000:
                diff_list.append((s, abs(ce-pe)))

        if not diff_list:
            st.error("No ATM found")
            st.stop()

        atm_strike = min(diff_list, key=lambda x: x[1])[0]

        # =====================================================
        # 📊 16 RULES (UNCHANGED LOGIC)
        # =====================================================
        with tab2:
            rows = []

            ce = get_price("CE", strike)
            pe = get_price("PE", strike)

            if ce and pe:
                rows.append(["A", (ce+pe)/2, "A", (ce+pe)/2])

            ce = get_price("CE", strike+100)
            pe = get_price("PE", strike-100)
            if ce and pe:
                rows.append(["B", (ce+pe)/2, "B", (ce+pe)/2])

            for step in [150,200]:
                ce = get_price("CE", strike+step)
                pe = get_price("PE", strike-step)
                if ce and pe:
                    rows.append([strike-step, (ce+pe)/2, strike+step, (ce+pe)/2])

            table_df = pd.DataFrame(rows, columns=["Name","CE","Name ","PE"])
            st.dataframe(table_df)

        # =====================================================
        # 📊 AVERAGE ONLY
        # =====================================================
        with tab3:
            all_strikes = sorted(strikes)
            idx = min(range(len(all_strikes)), key=lambda i: abs(all_strikes[i] - atm_strike))
            selected = all_strikes[max(0, idx-24): idx+25]

            avg_rows = []
            for s in selected:
                ce = get_price("CE", s)
                pe = get_price("PE", s)
                if ce and pe:
                    avg_rows.append([int(s), round((ce+pe)/2,2)])

            st.dataframe(pd.DataFrame(avg_rows, columns=["Strike","Average"]))

        # =====================================================
        # 🔄 SEE-SAW
        # =====================================================
        with tab4:

            mapping = []
            all_strikes = sorted(strikes)

            idx = min(range(len(all_strikes)), key=lambda i: abs(all_strikes[i] - atm_strike))
            selected = all_strikes[max(0, idx-20): idx+21]

            for s in selected:
                ce = get_price("CE", s-100)
                pe = get_price("PE", s+100)
                if ce and pe:
                    mapping.append([int(s), ce, pe])

            mapping_df = pd.DataFrame(mapping, columns=["Strike","Call","Put"])
            st.dataframe(mapping_df)

            call_list = []
            put_list = []

            for _, row in mapping_df.sort_values("Strike", ascending=False).iterrows():
                call_list.append(f"{int(row['Strike'])},{round(row['Put'],2)}")

            for _, row in mapping_df.sort_values("Strike").iterrows():
                put_list.append(f"{int(row['Strike'])},{round(row['Call'],2)}")

            call_string = "[" + ",".join(call_list) + "]"
            put_string = "[" + ",".join(put_list) + "]"

            st.session_state["call_data"] = call_string
            st.session_state["put_data"] = put_string

            st.text_area("CALL", call_string, height=100)
            st.text_area("PUT", put_string, height=100)

        # =====================================================
        # ⚡ GAP ADJUST
        # =====================================================
        with tab6:

            call_input = st.session_state.get("call_data")
            put_input = st.session_state.get("put_data")

            if not call_input or not put_input:
                st.warning("Run See-Saw first")
                st.stop()

            points = st.number_input("Points", value=100, step=50)
            gap_type = st.radio("Market", ["Gap Up","Gap Down"])

            if st.button("Adjust"):

                if gap_type == "Gap Up":
                    new_call = adjust_list(call_input, +points)
                    new_put = adjust_list(put_input, -points)
                else:
                    new_call = adjust_list(call_input, -points)
                    new_put = adjust_list(put_input, +points)

                col1, col2 = st.columns(2)

                with col1:
                    st.code(new_call)

                with col2:
                    st.code(new_put)

# =====================================================
# 📊 STRIKES SOLD
# =====================================================
elif page == "📊 Strikes Sold":

    st.title("📊 Strikes Sold")

    prev_file = st.file_uploader("Prev File")
    mw_file = st.file_uploader("MW File")

    if prev_file and mw_file:
        df_prev = safe_read(prev_file)
        df_mw = safe_read(mw_file)

        st.success("Files Loaded")
