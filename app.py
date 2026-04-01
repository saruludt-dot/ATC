import streamlit as st
import pandas as pd
import base64

# ----------- LOGIN SYSTEM -----------

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
                st.error("Invalid username or password")

        return False

    return True

if not check_login():
    st.stop()

# ----------- SIDEBAR -----------

st.sidebar.subheader("📊 Display Options")
show_table1 = st.sidebar.checkbox("Average Calculation", True)
show_table2 = st.sidebar.checkbox("See-Saw Calculation", True)
show_variations = st.sidebar.checkbox("Variations", True)

# ----------- LOGO -----------

def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

logo_base64 = get_base64_image("logo.png")

st.markdown(f"""
<img src="data:image/png;base64,{logo_base64}" 
     style="width:40%; display:block; margin:auto;">
""", unsafe_allow_html=True)

# ----------- TABS -----------

tab1, tab2, tab3, tab4 = st.tabs([
    "📥 Input",
    "📊 Average",
    "🔄 See-Saw",
    "📊 Variations"
])

# ----------- INPUT TAB -----------

with tab1:

    uploaded_file = st.file_uploader("📂 Upload CSV file", type=["csv"])

    col1, col2 = st.columns(2)

    with col1:
        expiry = st.date_input("📅 Expiry Date")

    with col2:
        strike = st.number_input("💰 Strike Price", step=50)

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
    unique_strikes = df[df["Expiry Date"] == expiry_str]["Strike Price"].unique()

    for s in unique_strikes:
        ce = get_price("CE", s)
        pe = get_price("PE", s)

        if ce is not None and pe is not None:
            diff_list.append((s, ce, pe, abs(ce - pe)))

    if diff_list:
        atm_strike, atm_ce, atm_pe, _ = min(diff_list, key=lambda x: x[3])

    # ----------- TABLE 1 -----------

    rows = []

    # ----------- A -----------
    ce = get_price("CE", strike)
    pe = get_price("PE", strike)

    if ce is not None and pe is not None:
        val = round((ce + pe) / 2, 2)
        rows.append(["A", f"{val:.2f}", "A", f"{val:.2f}"])

    # ----------- B -----------
    ce = get_price("CE", strike + 100)
    pe = get_price("PE", strike - 100)

    if ce is not None and pe is not None:
        val = round((ce + pe) / 2, 2)
        rows.append(["B", f"{val:.2f}", "B", f"{val:.2f}"])

    # ----------- C & D -----------
    for step in [150, 200]:

        ce_price = get_price("CE", strike + step)
        pe_price = get_price("PE", strike - step)

        if ce_price and pe_price:
            val = round((ce_price + pe_price) / 2, 2)

            left = int(strike - step)
            right = int(strike + step)

            rows.append([left, f"{val:.2f}", right, f"{val:.2f}"])

    # ----------- C3, C4, C5 -----------
    ce_close = get_price("CE", strike)
    pe_close = get_price("PE", strike)

    if ce_close is not None and pe_close is not None:

        c3_ce = round(ce_close / 4, 2)
        c4_ce = round(ce_close * 0.10, 2)
        c5_ce = round(ce_close * 0.01, 2)

        c3_pe = round(pe_close / 4, 2)
        c4_pe = round(pe_close * 0.10, 2)
        c5_pe = round(pe_close * 0.01, 2)

        rows.append(["C3", c3_ce, "C3", c3_pe])
        rows.append(["C4", c4_ce, "C4", c4_pe])
        rows.append(["C5", c5_ce, "C5", c5_pe])

    # ----------- E to I -----------
    for step in [50, 100, 150, 200, 250]:

        ce_price = get_price("CE", strike - step)
        pe_price = get_price("PE", strike + step)

        if ce_price and pe_price:
            val = round((ce_price + pe_price) / 2, 2)

            left = int(strike + step)
            right = int(strike - step)

            rows.append([left, f"{val:.2f}", right, f"{val:.2f}"])

    # ----------- PRICE DETAILS -----------

    ce_row = df[
        (df["Expiry Date"] == expiry_str) &
        (df["Option Type"] == "CE") &
        (df["Strike Price"] == strike)
    ]

    pe_row = df[
        (df["Expiry Date"] == expiry_str) &
        (df["Option Type"] == "PE") &
        (df["Strike Price"] == strike)
    ]

    if not ce_row.empty and not pe_row.empty:

        ce_close = ce_row.iloc[0]["Close Price"]
        ce_high = ce_row.iloc[0]["High Price"]
        ce_low = ce_row.iloc[0]["Low Price"]

        pe_close = pe_row.iloc[0]["Close Price"]
        pe_high = pe_row.iloc[0]["High Price"]
        pe_low = pe_row.iloc[0]["Low Price"]

        rows.append(["Close", f"{ce_close:.2f}", "Close", f"{pe_close:.2f}"])
        rows.append(["High", f"{ce_high:.2f}", "High", f"{pe_high:.2f}"])
        rows.append(["Low", f"{ce_low:.2f}", "Low", f"{pe_low:.2f}"])

    # ----------- FINAL CLOSE ROW -----------
    
    if ce_close and pe_close:
        rows.append([
            f"{int(strike)} PE Close", f"{pe_close:.2f}",
            f"{int(strike)} CE Close", f"{ce_close:.2f}"
        ])

    # ----------- DATAFRAME -----------

    table_df = pd.DataFrame(rows, columns=["Name", "CE", "Name ", "PE"]).astype(str)

    # ----------- STYLING -----------

    def highlight_rows(row):
        label = str(row["Name"])

        if label in ["A", "B"]:
            return ["border-left: 4px solid #2ecc71"] * len(row)

        if label in ["C3", "C4", "C5"]:
            return ["border-left: 4px solid #f39c12"] * len(row)

        if label in ["Close", "High", "Low"]:
            return ["border-left: 4px solid #8e44ad"] * len(row)

        return [""] * len(row)

    styled_df = table_df.style.apply(highlight_rows, axis=1)

    # ----------- DISPLAY -----------

    if show_table1:
        st.markdown("### 📊 Average Calculation")
        st.dataframe(styled_df, width='stretch')
        st.divider()


    # -------- SEE-SAW --------

    mapping_rows = []

    all_strikes = sorted(unique_strikes)

    if len(all_strikes) > 0:
        closest_idx = min(range(len(all_strikes)), key=lambda i: abs(all_strikes[i] - strike))

        for s in all_strikes[max(0, closest_idx-5):closest_idx+5]:
            pe_shift = get_price("PE", s + 100)
            ce_shift = get_price("CE", s - 100)

            if pe_shift is not None and ce_shift is not None:
                mapping_rows.append([int(s), pe_shift, ce_shift])

    mapping_df = pd.DataFrame(mapping_rows, columns=["Strike", "Call", "Put"])

# -------- TAB 2 --------

    with tab2:
        if show_table1:
            st.subheader("📊 Average")
            st.dataframe(table_df)

# -------- TAB 3 --------

    with tab3:
        if show_table2:
            st.subheader("🔄 See-Saw")
            st.dataframe(mapping_df)

        if 'atm_strike' in locals():

            st.subheader("📍 ATM")
            st.success(f"{atm_strike}")

            ce_bep = get_price("CE", atm_strike - 100)
            pe_bep = get_price("PE", atm_strike + 100)

            if ce_bep is not None and pe_bep is not None:
                bep = round((ce_bep + pe_bep) / 2, 2)
                st.subheader("💰 BEP")
                st.success(f"{bep}")

# -------- TAB 4 --------

    with tab4:
        if show_variations:
            st.subheader("📊 Variations")
            st.write("Variation logic here")
