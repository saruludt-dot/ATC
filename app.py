import streamlit as st
import pandas as pd
import base64
import streamlit.components.v1 as components

# -------- LOGIN --------
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔐 Login Required")

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            if u == "ATC" and p == "2015":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid login")

        return False
    return True

if not check_login():
    st.stop()

if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# -------- LOGO LEFT --------
def get_img(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

col_logo, col_tabs = st.columns([2,6])

with col_logo:
    logo = get_img("logo.png")
    st.markdown(f"<img src='data:image/png;base64,{logo}' width='100%'>", unsafe_allow_html=True)

# -------- TABS --------
with col_tabs:
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Input", "📊 Average", "🔄 See-Saw", "📊 Variations"
    ])

# -------- INPUT --------
with tab1:
    uploaded_file = st.file_uploader("Upload CSV")
    expiry = st.date_input("Expiry Date")
    strike = st.number_input("Strike", step=50)
    calculate = st.button("Calculate")

# -------- MAIN LOGIC --------
if uploaded_file and calculate:

    df = pd.read_csv(uploaded_file, on_bad_lines='skip', engine='python')

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

    # -------- ATM --------
    diff_list = []
    strikes = df[df["Expiry Date"]==expiry_str]["Strike Price"].unique()

    for s in strikes:
        ce = get_price("CE", s)
        pe = get_price("PE", s)
        if ce and pe and 10 < ce < 1000 and 10 < pe < 1000:
            diff_list.append((s, ce, pe, abs(ce-pe)))

    if diff_list:
        atm_strike, atm_ce, atm_pe, _ = min(diff_list, key=lambda x: x[3])

    # -------- TABLE 1 --------
    rows = []

    # A
    ce = get_price("CE", strike)
    pe = get_price("PE", strike)
    if ce and pe and 10 < ce < 1000 and 10 < pe < 1000:
        val = (ce+pe)/2
        rows.append(["A", f"{val:.2f}", "A", f"{val:.2f}"])

    # B
    ce = get_price("CE", strike+100)
    pe = get_price("PE", strike-100)
    if ce and pe and 10 < ce < 1000 and 10 < pe < 1000:
        val = (ce+pe)/2
        rows.append(["B", f"{val:.2f}", "B", f"{val:.2f}"])

    # C D
    for step in [150,200]:
        ce = get_price("CE", strike+step)
        pe = get_price("PE", strike-step)
        if ce is not None and pe is not None:
            val = (ce+pe)/2
            rows.append([strike-step, f"{val:.2f}", strike+step, f"{val:.2f}"])

    # C3 C4 C5
    ce_close = get_price("CE", strike)
    pe_close = get_price("PE", strike)

    if ce_close and pe_close:
        rows.append(["C3", f"{ce_close/4:.2f}", "C3", f"{pe_close/4:.2f}"])
        rows.append(["C4", f"{ce_close*0.1:.2f}", "C4", f"{pe_close*0.1:.2f}"])
        rows.append(["C5", f"{ce_close*0.01:.2f}", "C5", f"{pe_close*0.01:.2f}"])

    # E-I
    for step in [50,100,150,200,250]:
        ce = get_price("CE", strike-step)
        pe = get_price("PE", strike+step)
        if ce is not None and pe is not None:
            val = (ce+pe)/2
            rows.append([strike+step, f"{val:.2f}", strike-step, f"{val:.2f}"])

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

    table_df = pd.DataFrame(rows, columns=["Name","CE","Name ","PE"])

    # -------- SEE-SAW (HTML VERSION) --------

    mapping = []
    strikes = sorted(strikes)

    idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - strike))

    start = max(0, idx - 11)
    end = min(len(strikes), idx + 12)

    for s in strikes[start:end]:
        pe = get_price("PE", s + 100)
        ce = get_price("CE", s - 100)

        if pe is not None and ce is not None:
            mapping.append([int(s), ce, pe])

    mapping_df = pd.DataFrame(mapping, columns=["Strike", "Call", "Put"])

    # -------- BUILD HTML TABLE --------

    html = """<style>
    .table-container {
        width: 100%;
        overflow-x: auto;
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }
    .custom-table th {
        background-color: #111827;
        color: white;
        padding: 10px;
        text-align: center;
    }
    .custom-table td {
        padding: 8px;
        text-align: center;
        border-bottom: 1px solid #333;
    }
    </style>

    <div class="table-container">
    <table class="custom-table">
    <tr>
    <th>Strike</th>
    <th>Call</th>
    <th>Put</th>
    </tr>
    """

    for _, row in mapping_df.iterrows():
        s = int(row["Strike"])

        # 🎨 COLOR LOGIC
        color = ""
        text_color = "white"
        
        if 'atm_strike' in locals():
            if s == int(atm_strike):
                color = "#fff3cd"   # Yellow
            elif s == int(atm_strike + 100):
                color = "#d4edda"   # Green
            elif s == int(atm_strike - 100):
                color = "#f8d7da"   # Red

        html += f"""
    <tr style="background-color:{color}; color:{text_color}; font-weight:bold;">
        <td>{s}</td>
        <td>{row['Call']:.2f}</td>
        <td>{row['Put']:.2f}</td>
    </tr>
    """

    html += "</table></div>"

    # -------- DISPLAY --------
    #st.markdown("### 🔄 See-Saw Calculation", unsafe_allow_html=True)
    #st.markdown(html, unsafe_allow_html=True)
    

    # -------- TAB 2 --------
    with tab2:
        st.dataframe(table_df)

    # ----------- TAB 3 : SEE-SAW + RESULTS -----------
    with tab3:

        if uploaded_file and calculate:

            st.subheader("🔄 See-Saw Calculation")

            # ✅ CORRECT DISPLAY
            components.html(html, height=600, scrolling=True)

            # ----------- ATM / BEP / CHARTS -----------

            if 'atm_strike' in locals():

                diff = round(atm_ce - atm_pe, 2)

                st.subheader("📍 Minimum Difference Strike (ATM)")
                st.success(
                    f"Strike: {int(atm_strike)} | CE: {atm_ce:.2f} | PE: {atm_pe:.2f} | Diff: {diff:.2f}"
                )

                st.divider()

                ce_bep = get_price("CE", atm_strike - 100)
                pe_bep = get_price("PE", atm_strike + 100)

                if ce_bep is not None and pe_bep is not None and ce_bep > 0 and pe_bep > 0:
                    bep = round((ce_bep + pe_bep) / 2, 2)

                    st.subheader("💰 BEP")
                    st.success(f"{bep:.2f}")

                st.divider()

                st.subheader("📈 Charts to be Used")

                col1, col2 = st.columns(2)

                with col1:
                    st.success(f"🟢 NIFTY {expiry_str} CE {int(atm_strike - 100)}")

                with col2:
                    st.error(f"🔴 NIFTY {expiry_str} PE {int(atm_strike + 100)}")
    
    

    # -------- VARIATIONS --------
    with tab4:

        ce_data, pe_data = [], []

        if 'atm_strike' in locals():

            idx = min(range(len(strikes)), key=lambda i: abs(strikes[i]-atm_strike))

            for s in strikes[max(0,idx-10):idx+10]:
                ce = df[(df["Option Type"]=="CE") & (df["Strike Price"]==s)]
                pe = df[(df["Option Type"]=="PE") & (df["Strike Price"]==s)]

                ce_data.append([s, ce.iloc[0]["High Price"] if not ce.empty else None,
                                  ce.iloc[0]["Low Price"] if not ce.empty else None])

                pe_data.append([s, pe.iloc[0]["High Price"] if not pe.empty else None,
                                  pe.iloc[0]["Low Price"] if not pe.empty else None])

            ce_df = pd.DataFrame(ce_data, columns=["Strike","High","Low"])
            pe_df = pd.DataFrame(pe_data, columns=["Strike","High","Low"])

            col1,col2 = st.columns(2)
            col1.dataframe(ce_df)
            col2.dataframe(pe_df)
