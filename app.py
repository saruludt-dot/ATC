import streamlit as st
import pandas as pd
import base64
import streamlit.components.v1 as components

# =========================
# SESSION INIT
# =========================
if "calculated" not in st.session_state:
    st.session_state.update({
        "calculated": False,
        "uploaded_file": None,
        "expiry": None,
        "strike": None,
        "call_data": None,
        "put_data": None
    })

# =========================
# HELPERS
# =========================
def safe_read_csv(file):
    if file is None:
        return None
    file.seek(0)
    return pd.read_csv(file, on_bad_lines='skip', engine='python')

def parse_option_list(data, change):
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
            expiry = st.date_input("Expiry")

        with col3:
            strike = st.number_input("Strike", step=50)

        calculate = st.button("🚀 Calculate", use_container_width=True)

        if calculate:
            st.session_state["calculated"] = True
            st.session_state["uploaded_file"] = uploaded_file
            st.session_state["expiry"] = expiry
            st.session_state["strike"] = strike

    # ---------------- LOAD STATE ----------------
    uploaded_file = st.session_state.get("uploaded_file")
    expiry = st.session_state.get("expiry")
    strike = st.session_state.get("strike")

    if uploaded_file and st.session_state["calculated"]:

        df = safe_read_csv(uploaded_file)

        df.columns = df.columns.str.strip()
        df["Expiry Date"] = df["Expiry Date"].astype(str).str.strip()
        df["Option Type"] = df["Option Type"].str.upper()

        df["Strike Price"] = df["Strike Price"].astype(str).str.replace(",", "").astype(float)
        df["Close Price"] = pd.to_numeric(df["Close Price"], errors="coerce")

        expiry_str = expiry.strftime("%d-%b-%Y")

        def get_price(opt, s):
            r = df[(df["Expiry Date"] == expiry_str) &
                   (df["Option Type"] == opt) &
                   (df["Strike Price"] == s)]
            return r.iloc[0]["Close Price"] if not r.empty else None

        # ---------------- SEE-SAW TAB ----------------
        with tab4:

            st.subheader("🔄 See-Saw")

            mapping = []
            strikes = sorted(df["Strike Price"].dropna().unique())

            for s in strikes:
                ce = get_price("CE", s - 100)
                pe = get_price("PE", s + 100)

                if ce and pe:
                    mapping.append([int(s), ce, pe])

            mapping_df = pd.DataFrame(mapping, columns=["Strike", "Call", "Put"])
            st.dataframe(mapping_df)

            # -------- TradingView Format --------
            call_list = []
            put_list = []

            for _, row in mapping_df.sort_values("Strike", ascending=False).iterrows():
                call_list.append(f"{int(row['Strike'])},{round(row['Put'],2)}")

            for _, row in mapping_df.sort_values("Strike").iterrows():
                put_list.append(f"{int(row['Strike'])},{round(row['Call'],2)}")

            call_string = "[" + ",".join(call_list) + "]"
            put_string = "[" + ",".join(put_list) + "]"

            # ✅ STORE FOR GAP TAB
            st.session_state["call_data"] = call_string
            st.session_state["put_data"] = put_string

            col1, col2 = st.columns(2)

            with col1:
                st.text_area("CALL", call_string, height=120)

            with col2:
                st.text_area("PUT", put_string, height=120)

        # ---------------- GAP TAB ----------------
        with tab6:

            st.subheader("⚡ Gap Adjustment")

            call_input = st.session_state.get("call_data")
            put_input = st.session_state.get("put_data")

            if not call_input or not put_input:
                st.warning("Run See-Saw first")
                st.stop()

            points = st.number_input("Points", value=100, step=50)

            gap_type = st.radio("Market", ["Gap Up", "Gap Down"])

            if st.button("Adjust"):

                if gap_type == "Gap Up":
                    new_call = parse_option_list(call_input, +points)
                    new_put = parse_option_list(put_input, -points)
                else:
                    new_call = parse_option_list(call_input, -points)
                    new_put = parse_option_list(put_input, +points)

                col1, col2 = st.columns(2)

                with col1:
                    st.code(new_call)

                with col2:
                    st.code(new_put)

# =====================================================
# 📊 STRIKES SOLD (UNCHANGED SAFE)
# =====================================================
elif page == "📊 Strikes Sold":

    st.title("📊 Strikes Sold")

    prev_file = st.file_uploader("Prev File")
    mw_file = st.file_uploader("MW File")

    if prev_file and mw_file:

        df_prev = safe_read_csv(prev_file)
        df_mw = safe_read_csv(mw_file)

        st.success("Files loaded successfully")
