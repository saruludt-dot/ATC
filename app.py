import streamlit as st
import pandas as pd
import base64

# ----------- LOGIN -----------

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔐 Login Required")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username == "ATC" and password == "2015":
                st.session_state.logged_in = True
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid username")

        return False
    return True

if not check_login():
    st.stop()

# ----------- LOGOUT -----------

if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ----------- LOGO -----------

def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

logo = get_base64_image("logo.png")

st.markdown(f"""
<img src="data:image/png;base64,{logo}" style="width:35%;display:block;margin:auto;">
""", unsafe_allow_html=True)

# ----------- TABS -----------

tab1, tab2, tab3, tab4 = st.tabs([
    "📥 Input",
    "📊 Average",
    "🔄 See-Saw",
    "📊 Variations"
])

# ----------- INPUT -----------

with tab1:

    uploaded_file = st.file_uploader("📂 Upload CSV", type=["csv"])

    col1, col2 = st.columns(2)

    with col1:
        expiry = st.date_input("📅 Expiry Date")

    with col2:
        strike = st.number_input("💰 Strike", step=50)

    calculate = st.button("🚀 Calculate")

# ----------- MAIN LOGIC -----------

if uploaded_file and calculate:

    df = pd.read_csv(uploaded_file, on_bad_lines='skip', engine='python')

    df.columns = df.columns.str.strip()
    df["Expiry Date"] = df["Expiry Date"].astype(str).str.strip()
    df["Option Type"] = df["Option Type"].astype(str).str.strip().str.upper()

    df["Strike Price"] = df["Strike Price"].astype(str).str.replace(",", "").astype(float)

    df["Close Price"] = pd.to_numeric(df["Close Price"], errors="coerce")
    df["High Price"] = pd.to_numeric(df["High Price"], errors="coerce")
    df["Low Price"] = pd.to_numeric(df["Low Price"], errors="coerce")

    expiry_str = expiry.strftime("%d-%b-%Y")

    def get_price(option, strike_val):
        row = df[
            (df["Expiry Date"] == expiry_str) &
            (df["Option Type"] == option) &
            (df["Strike Price"] == strike_val)
        ]
        return row.iloc[0]["Close Price"] if not row.empty else None

    # -------- ATM --------

    diff_list = []
    strikes = df[df["Expiry Date"] == expiry_str]["Strike Price"].unique()

    for s in strikes:
        ce = get_price("CE", s)
        pe = get_price("PE", s)

        if ce is not None and pe is not None:
            diff_list.append((s, ce, pe, abs(ce - pe)))

    if diff_list:
        atm_strike, atm_ce, atm_pe, _ = min(diff_list, key=lambda x: x[3])

    # ----------- TABLE 1 -----------

    rows = []

    # A
    ce = get_price("CE", strike)
    pe = get_price("PE", strike)

    if ce is not None and pe is not None:
        val = round((ce + pe) / 2, 2)
        rows.append(["A", f"{val:.2f}", "A", f"{val:.2f}"])

    # B
    ce = get_price("CE", strike + 100)
    pe = get_price("PE", strike - 100)

    if ce is not None and pe is not None:
        val = round((ce + pe) / 2, 2)
        rows.append(["B", f"{val:.2f}", "B", f"{val:.2f}"])

    # C & D
    for step in [150, 200]:
        ce_p = get_price("CE", strike + step)
        pe_p = get_price("PE", strike - step)

        if ce_p is not None and pe_p is not None:
            val = round((ce_p + pe_p) / 2, 2)
            rows.append([int(strike-step), f"{val:.2f}", int(strike+step), f"{val:.2f}"])

    # C3 C4 C5
    ce_close = get_price("CE", strike)
    pe_close = get_price("PE", strike)

    if ce_close is not None and pe_close is not None:
        rows.append(["C3", f"{ce_close/4:.2f}", "C3", f"{pe_close/4:.2f}"])
        rows.append(["C4", f"{ce_close*0.10:.2f}", "C4", f"{pe_close*0.10:.2f}"])
        rows.append(["C5", f"{ce_close*0.01:.2f}", "C5", f"{pe_close*0.01:.2f}"])

    # E to I
    for step in [50, 100, 150, 200, 250]:
        ce_p = get_price("CE", strike - step)
        pe_p = get_price("PE", strike + step)

        if ce_p is not None and pe_p is not None:
            val = round((ce_p + pe_p) / 2, 2)
            rows.append([int(strike+step), f"{val:.2f}", int(strike-step), f"{val:.2f}"])

    # Close High Low
    ce_row = df[(df["Option Type"]=="CE") & (df["Strike Price"]==strike)]
    pe_row = df[(df["Option Type"]=="PE") & (df["Strike Price"]==strike)]

    if not ce_row.empty and not pe_row.empty:
        rows.append(["Close", f"{ce_row.iloc[0]['Close Price']:.2f}",
                     "Close", f"{pe_row.iloc[0]['Close Price']:.2f}"])

        rows.append(["High", f"{ce_row.iloc[0]['High Price']:.2f}",
                     "High", f"{pe_row.iloc[0]['High Price']:.2f}"])

        rows.append(["Low", f"{ce_row.iloc[0]['Low Price']:.2f}",
                     "Low", f"{pe_row.iloc[0]['Low Price']:.2f}"])

    if ce_close and pe_close:
        rows.append([
            f"{int(strike)} PE Close", f"{pe_close:.2f}",
            f"{int(strike)} CE Close", f"{ce_close:.2f}"
        ])

    table_df = pd.DataFrame(rows, columns=["Name", "CE", "Name ", "PE"])

    # -------- SEE-SAW --------

    mapping = []
    strikes = sorted(strikes)

    if len(strikes) > 0:
        idx = min(range(len(strikes)), key=lambda i: abs(strikes[i]-strike))

        for s in strikes[max(0, idx-5):idx+5]:
            pe_s = get_price("PE", s+100)
            ce_s = get_price("CE", s-100)

            if pe_s is not None and ce_s is not None:
                mapping.append([int(s), f"{pe_s:.2f}", f"{ce_s:.2f}"])

    mapping_df = pd.DataFrame(mapping, columns=["Strike", "Call", "Put"])

    # -------- VARIATIONS --------

    ce_data, pe_data = [], []

    if 'atm_strike' in locals():

        all_strikes = sorted(strikes)
        idx = min(range(len(all_strikes)), key=lambda i: abs(all_strikes[i]-atm_strike))

        for s in all_strikes[max(0, idx-10):idx+10]:

            ce_row = df[(df["Option Type"]=="CE") & (df["Strike Price"]==s)]
            pe_row = df[(df["Option Type"]=="PE") & (df["Strike Price"]==s)]

            ce_high = ce_row.iloc[0]["High Price"] if not ce_row.empty else None
            ce_low = ce_row.iloc[0]["Low Price"] if not ce_row.empty else None

            pe_high = pe_row.iloc[0]["High Price"] if not pe_row.empty else None
            pe_low = pe_row.iloc[0]["Low Price"] if not pe_row.empty else None

            ce_data.append([s, ce_high, ce_low])
            pe_data.append([s, pe_high, pe_low])

        ce_df = pd.DataFrame(ce_data, columns=["Strike","High","Low"])
        pe_df = pd.DataFrame(pe_data, columns=["Strike","High","Low"])

    # -------- TAB 2 --------

    with tab2:
        st.subheader("📊 Average")
        st.dataframe(table_df)

    # -------- TAB 3 --------

    with tab3:
        st.subheader("🔄 See-Saw")
        st.dataframe(mapping_df)

        if 'atm_strike' in locals():
            st.subheader("📍 ATM")
            st.success(atm_strike)

            ce_bep = get_price("CE", atm_strike-100)
            pe_bep = get_price("PE", atm_strike+100)

            if ce_bep and pe_bep:
                st.subheader("💰 BEP")
                st.success(round((ce_bep+pe_bep)/2,2))

    # -------- TAB 4 --------

    with tab4:
        st.subheader("📊 Variations")

        col1, col2 = st.columns(2)

        with col1:
            st.write("CE")
            st.dataframe(ce_df)

        with col2:
            st.write("PE")
            st.dataframe(pe_df)
