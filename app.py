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

# ----------- LOGOUT -----------

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ----------- SIDEBAR -----------

st.sidebar.subheader("📊 Display Options")

show_table1 = st.sidebar.checkbox("Average Calculation", True)
show_table2 = st.sidebar.checkbox("See-Saw Calculation", True)
show_atm = st.sidebar.checkbox("Minimum Difference Strike", True)
show_bep = st.sidebar.checkbox("BEP", True)
show_chart_info = st.sidebar.checkbox("Charts to be Used", True)
show_variations = st.sidebar.checkbox("Variations", True)

# ----------- LAYOUT -----------

col_left, col_right = st.columns([3,5])

# ----------- LOGO -----------

def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

logo_base64 = get_base64_image("logo.png")

with col_left:
    st.markdown(f"""
    <img src="data:image/png;base64,{logo_base64}" 
         style="width:100%; height:auto;">
    """, unsafe_allow_html=True)

# ----------- INPUT PANEL -----------

with col_right:

    st.markdown("""
    <div style='
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(0,255,204,0.2);
    '>
    """, unsafe_allow_html=True)

    st.markdown("### 📥 Input")

    uploaded_file = st.file_uploader("📂 Upload CSV file", type=["csv"])

    col1, col2, col3 = st.columns(3)

    with col1:
        expiry = st.date_input("📅 Expiry Date")

    with col2:
        strike = st.number_input("💰 Strike Price", step=50)

    with col3:
        option = st.radio("📊 Option Type", ["CE", "PE"], horizontal=True)

    colA, colB, colC = st.columns([1,2,1])
    with colB:
        calculate = st.button("🚀 Calculate Values")

    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ----------- MAIN LOGIC -----------

if uploaded_file and calculate:

    df = pd.read_csv(uploaded_file)

    df.columns = df.columns.str.strip()
    df["Expiry Date"] = df["Expiry Date"].astype(str).str.strip()
    df["Option Type"] = df["Option Type"].astype(str).str.strip().str.upper()

    df["Strike Price"] = df["Strike Price"].astype(str).str.replace(",", "").astype(float)

    df["Close Price"] = pd.to_numeric(
        df["Close Price"].astype(str).str.replace(",", "").replace("-", ""),
        errors="coerce"
    )

    df["High Price"] = pd.to_numeric(
        df["High Price"].astype(str).str.replace(",", "").replace("-", ""),
        errors="coerce"
    )

    df["Low Price"] = pd.to_numeric(
        df["Low Price"].astype(str).str.replace(",", "").replace("-", ""),
        errors="coerce"
    )

    expiry_str = expiry.strftime("%d-%b-%Y")

    def get_price(option, strike_val):
        row = df[
            (df["Expiry Date"] == expiry_str) &
            (df["Option Type"] == option) &
            (df["Strike Price"] == strike_val)
        ]
        return row.iloc[0]["Close Price"] if not row.empty else None

    # ----------- ATM -----------

    diff_list = []
    unique_strikes = df[df["Expiry Date"] == expiry_str]["Strike Price"].unique()

    for s in unique_strikes:
        ce = get_price("CE", s)
        pe = get_price("PE", s)

        if ce and pe and 10 < ce < 1000 and 10 < pe < 1000:
            diff_list.append((s, ce, pe, abs(ce - pe)))

    if diff_list:
        atm_strike, atm_ce, atm_pe, atm_diff = min(diff_list, key=lambda x: x[3])

        #if show_atm:
            #diff = round(atm_ce - atm_pe, 2)
            #st.subheader("📍 Minimum Difference Strike (ATM)")
            #st.success(f"Strike: {int(atm_strike)} | CE: {atm_ce:.2f} | PE: {atm_pe:.2f} | Diff: {diff:.2f}")

        #st.divider()

    # ----------- TABLE 1 -----------

    rows = []

    # ----------- A -----------
    ce = get_price("CE", strike)
    pe = get_price("PE", strike)

    if ce and pe:
        val = round((ce + pe) / 2, 2)
        rows.append(["A", f"{val:.2f}", "A", f"{val:.2f}"])

    # ----------- B -----------
    ce = get_price("CE", strike + 100)
    pe = get_price("PE", strike - 100)

    if ce and pe:
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

    # ----------- TABLE 2 -----------

    mapping_rows = []
    all_strikes = sorted(df[df["Expiry Date"] == expiry_str]["Strike Price"].unique())

    if len(all_strikes) > 0 and strike:

        closest_idx = min(range(len(all_strikes)), key=lambda i: abs(all_strikes[i] - strike))

        start = max(0, closest_idx - 12)
        end = min(len(all_strikes), closest_idx + 13)

        for s in all_strikes[start:end]:
            pe_shift = get_price("PE", s + 100)
            ce_shift = get_price("CE", s - 100)

            if pe_shift is not None and ce_shift is not None:
                mapping_rows.append([int(s), f"{pe_shift:.2f}", f"{ce_shift:.2f}"])

    mapping_df = pd.DataFrame(
        mapping_rows, columns=["Strike", "Call Price", "Put Price"]
    )

    # 👉 Convert to string (prevents right align)
    mapping_df["Strike"] = mapping_df["Strike"].astype(str)

    # 👉 Apply left alignment
    mapping_df = mapping_df.style.set_properties(
        subset=["Strike"], **{"text-align": "left"}
    )

    if show_table2:
        st.markdown("### 🔄 See-Saw Calculation")
        st.dataframe(mapping_df, width='stretch', hide_index=True)
        st.divider()

    # ----------- RIGHT SIDE RESULTS -----------

    if 'atm_strike' in locals():

        # 1️⃣ ATM RESULT
        if show_atm:
            diff = round(atm_ce - atm_pe, 2)
            st.subheader("📍 Minimum Difference Strike (ATM)")
            st.success(f"Strike: {int(atm_strike)} | CE: {atm_ce:.2f} | PE: {atm_pe:.2f} | Diff: {diff:.2f}")

        st.divider()

        # 2️⃣ BEP
        if show_bep:
            ce_bep = get_price("CE", atm_strike - 100)
            pe_bep = get_price("PE", atm_strike + 100)

            if ce_bep and pe_bep:
                bep = round((ce_bep + pe_bep) / 2, 2)
                st.subheader("💰 BEP")
                st.success(f"{bep:.2f}")

        st.divider()

        # 3️⃣ CHARTS
        if show_chart_info:
            st.subheader("📈 Charts to be Used")

            col1, col2 = st.columns(2)

            with col1:
                st.success(f"🟢 NIFTY {expiry_str} CE {int(atm_strike - 100)}")

            with col2:
                st.error(f"🔴 NIFTY {expiry_str} PE {int(atm_strike + 100)}")

        st.divider()

    # ----------- VARIATIONS (MAIN SCREEN) -----------

    if show_variations and 'atm_strike' in locals():

        st.markdown("### 📊 Variations")

        all_strikes = sorted(
            df[df["Expiry Date"] == expiry_str]["Strike Price"].unique()
        )

        if len(all_strikes) > 0:

            atm_idx = min(
                range(len(all_strikes)),
                key=lambda i: abs(all_strikes[i] - atm_strike)
            )

            start = max(0, atm_idx - 10)
            end = min(len(all_strikes), atm_idx + 11)

            selected_strikes = all_strikes[start:end]

            ce_data, pe_data = [], []

            for s in selected_strikes:

                ce_row = df[
                    (df["Expiry Date"] == expiry_str) &
                    (df["Option Type"] == "CE") &
                    (df["Strike Price"] == s)
                ]

                pe_row = df[
                    (df["Expiry Date"] == expiry_str) &
                    (df["Option Type"] == "PE") &
                    (df["Strike Price"] == s)
                ]

                ce_high = ce_row.iloc[0]["High Price"] if not ce_row.empty else None
                ce_low = ce_row.iloc[0]["Low Price"] if not ce_row.empty else None

                pe_high = pe_row.iloc[0]["High Price"] if not pe_row.empty else None
                pe_low = pe_row.iloc[0]["Low Price"] if not pe_row.empty else None

                ce_data.append([int(s), ce_high, ce_low])
                pe_data.append([int(s), pe_high, pe_low])

            ce_df = pd.DataFrame(ce_data, columns=["Strike", "High Price", "Low Price"])
            pe_df = pd.DataFrame(pe_data, columns=["Strike", "High Price", "Low Price"])

            # ✅ SAFE formatting (no astype)
            ce_df["High Price"] = ce_df["High Price"].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
            ce_df["Low Price"] = ce_df["Low Price"].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")

            pe_df["High Price"] = pe_df["High Price"].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
            pe_df["Low Price"] = pe_df["Low Price"].map(lambda x: f"{x:.2f}" if pd.notnull(x) else "")

        # ----------- HIGHLIGHT LOGIC -----------

        def highlight_ce(col):
            styles = []
            prev = None
            for val in col:
                if prev is not None and val is not None and val > prev:
                    styles.append("background-color:red")
                else:
                    styles.append("")
                prev = val
            return styles

        def highlight_pe(col):
            styles = []
            prev = None
            for val in col:
                if prev is not None and val is not None and val < prev:
                    styles.append("background-color:red")
                else:
                    styles.append("")
                prev = val
            return styles

        ce_styled = ce_df.style.apply(highlight_ce, subset=["High Price", "Low Price"])
        pe_styled = pe_df.style.apply(highlight_pe, subset=["High Price", "Low Price"])

        # ----------- DISPLAY SIDE BY SIDE -----------

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🟢 CE")
            st.dataframe(ce_styled, width='stretch', hide_index=True)

        with col2:
            st.markdown("#### 🔴 PE")
            st.dataframe(pe_styled, width='stretch', hide_index=True)

    # ----------- VARIATIONS -----------
    
    #if show_variations:
        #st.markdown("### 📊 Variations")

                
