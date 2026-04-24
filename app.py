import streamlit as st
import pandas as pd
import base64
import streamlit.components.v1 as components

if "show_success" not in st.session_state:
    st.session_state.show_success = False


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

page = st.sidebar.radio("", ["📈 Calculations", "📊 Strikes Sold"])

# =====================================================
# ✅ STRIKES SOLD (NEW LOGIC - DIRECT)
# =====================================================
if page == "📊 Strikes Sold":

    st.markdown("<h1>📈 Strikes Sold Today</h1><hr>", unsafe_allow_html=True)

    # ✅ ADD THIS
    expiry = st.date_input("📅 Select Expiry Date")
    expiry_str = expiry.strftime("%d-%b-%Y")

    prev_file = st.file_uploader("Upload Previous Day File", type=["csv"])
    mw_file = st.file_uploader("Upload Today MW File", type=["csv"])

    if prev_file is None or mw_file is None:
        st.info("Please upload both files")
        st.stop()

    # -------- PREVIOUS DAY --------
    df_prev = pd.read_csv(prev_file, on_bad_lines='skip', engine='python')

    df_prev.columns = df_prev.columns.str.strip()

    # ✅ ADD THIS
    df_prev["Expiry Date"] = df_prev["Expiry Date"].astype(str).str.strip()
    df_prev = df_prev[df_prev["Expiry Date"] == expiry_str]

    df_prev["Strike Price"] = df_prev["Strike Price"].astype(str).str.replace(",", "").astype(float)
    df_prev["Close Price"] = pd.to_numeric(df_prev["Close Price"], errors="coerce")
    df_prev["Option Type"] = df_prev["Option Type"].str.strip().str.upper()

    # -------- MW FILE --------
    df_mw = pd.read_csv(mw_file)
    df_mw.columns = df_mw.columns.str.strip().str.upper()

    # ✅ AUTO DETECT EXPIRY COLUMN
    expiry_col = next((col for col in df_mw.columns if "EXPIRY" in col), None)

    if expiry_col is None:
        st.error("❌ Expiry column not found")
        st.stop()

    # ✅ FILTER
    df_mw[expiry_col] = pd.to_datetime(df_mw[expiry_col], errors="coerce")
    selected_expiry = pd.to_datetime(expiry)

    df_mw = df_mw[df_mw[expiry_col] == selected_expiry]

    # EXISTING CODE
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

    st.markdown("""
        <div style='display:flex; align-items:center; gap:10px;'>
            <h1 style='margin:0;'>📈 Dashboard</h1>
        </div>
        <hr style='margin-top:5px;'>
    """, unsafe_allow_html=True)

    # -------- TABS --------
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 Input", "📊 16 Rules", "📊 Average Only", "🔄 See-Saw", "📊 Variations"
    ])

    # -------- INPUT --------
    with tab1:
        col1, col2, col3 = st.columns(3)

        with col1:
            uploaded_file = st.file_uploader("📥 Upload CSV")

        with col2:
            expiry = st.date_input("📅 Expiry Date")

        with col3:
            strike = st.number_input("🎯 Strike", step=50)
            
        calculate = st.button("🚀 Calculate", use_container_width=True)

        if calculate:
            st.session_state.show_success = True

        # ✅ MOVE HERE (ONLY INPUT TAB)
        if st.session_state.show_success:
            st.success("✅ Calculated")

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

        def get_left_label(s):
            if s == int(atm_strike):
                return "2nd Point: "
            elif s == int(atm_strike + 100):
                return "3rd Point: "
            elif s == int(atm_strike - 100):
                return "1st Point: "
            return ""

        def get_right_label(s):
            if s == int(atm_strike):
                return "2nd Point: "
            elif s == int(atm_strike + 100):
                return "1st Point: "   # swapped
            elif s == int(atm_strike - 100):
                return "3rd Point: "   # swapped
            return ""
        mapping = []
        strikes = sorted([s for s in strikes if pd.notnull(s)])

        if len(strikes) == 0:
            st.error("No valid strike data found")
            st.stop()

        idx = min(
            range(len(strikes)),
            key=lambda i: abs(float(strikes[i]) - float(atm_strike))
        )

        start = max(0, idx - 20)
        end = min(len(strikes), idx + 21)

        for s in strikes[start:end]:
            pe = get_price("PE", s + 100)
            ce = get_price("CE", s - 100)

            if pe is not None and ce is not None:
                mapping.append([int(s), ce, pe])

        mapping_df = pd.DataFrame(mapping, columns=["Strike", "Call", "Put"])

        # -------- BUILD HTML TABLE --------

        html = """
        <style>
        .table-container {
            width: 100%;
            height: 500px;           /* 🔥 FIXED HEIGHT for scroll */
            overflow-y: auto;
            border: 1px solid #333;
        }

        .custom-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        .custom-table th {
            position: sticky;        /* 🔥 FREEZE HEADER */
            top: 0;
            background-color: #ffc107;
            color: black;
            padding: 10px;
            text-align: center;
            z-index: 2;
            box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        }

        .custom-table td {
            padding: 8px;
            text-align: center;
            border-bottom: 2px solid #555;
        }
        </style>

        <div class="table-container">
        <table class="custom-table">
        <tr>
        <th>Strike</th>
        <th>Call</th>
        <th>Strike</th>
        <th>Put</th>
        </tr>
        """
        # ✅ SAFE GUARD (VERY IMPORTANT)
        if 'atm_strike' in locals() and 'mapping_df' in locals() and not mapping_df.empty:

            asc_df = mapping_df.sort_values(by="Strike").reset_index(drop=True)

            # Find ATM index safely
            atm_index = None
            for i, r in enumerate(asc_df.to_dict("records")):
                if int(r["Strike"]) == int(atm_strike):
                    atm_index = i
                    break

            if atm_index is not None:

                above = st.session_state.get("above", 14)
                below = st.session_state.get("below", 14)

                start = max(0, atm_index - 20)
                end = min(len(asc_df), atm_index + 21)

                asc_slice = asc_df.iloc[start:end].reset_index(drop=True)

                for i in range(len(asc_slice)):

                    # RIGHT SIDE (PUT)
                    right_strike = int(asc_slice.iloc[i]["Strike"])
                    right_put = asc_slice.iloc[i]["Call"]

                    # LEFT SIDE (CALL)
                    left_row = asc_slice.iloc[len(asc_slice) - 1 - i]
                    left_strike = int(left_row["Strike"])
                    left_call = left_row["Put"]

                    left_label = get_left_label(left_strike)
                    right_label = get_right_label(right_strike)

                    # COLOR LOGIC (keep your existing)
                    bg_color = "#111827"
                    text_color = "white"

                    if (left_strike == int(atm_strike) or right_strike == int(atm_strike)):
                        bg_color = "#fff3cd"; text_color = "black"
                    elif (left_strike == int(atm_strike + 100) or right_strike == int(atm_strike + 100)):
                        bg_color = "#d4edda"; text_color = "black"
                    elif (left_strike == int(atm_strike - 100) or right_strike == int(atm_strike - 100)):
                        bg_color = "#f8d7da"; text_color = "black"

                    html += f"""
        <tr style="background-color:{bg_color}; color:{text_color}; font-weight:bold;">
            <td>{left_label}{left_strike}</td>
            <td>{left_call:.2f}</td>
            <td>{right_label}{right_strike}</td>
            <td>{right_put:.2f}</td>
        </tr>
        """

        # -------- TAB 2 --------
        with tab2:
            st.dataframe(table_df)

            # ================================
            # 🔥 BUILD CE / PE STRING (16 RULES)
            # ================================

            ce_pairs = []
            pe_pairs = []

            for _, row in table_df.iterrows():

                name_ce = str(row["Name"]).strip()
                val_ce = row["CE"]

                name_pe = str(row["Name "]).strip()
                val_pe = row["PE"]

                # Skip empty
                if pd.notnull(val_ce):
                    ce_pairs.append(f"{name_ce}:{val_ce}")

                if pd.notnull(val_pe):
                    pe_pairs.append(f"{name_pe}:{val_pe}")

            # Final strings
            ce_string = ",".join(ce_pairs)
            pe_string = ",".join(pe_pairs)


            # ================================
            # 📌 TRADINGVIEW EXPORT UI
            # ================================

            st.subheader("📌 TradingView Export (16 Rules)")

            col1, col2 = st.columns(2)

            # 🟢 CE
            with col1:
                st.markdown("### 🟢 CE")

                components.html(f"""
                <textarea id="cebox" style="
                width:100%;
                height:70px;
                font-size:13px;
                padding:8px;
                box-sizing:border-box;">
                {ce_string}
                </textarea>

                <br><br>

                <button style="
                width:100%;
                height:45px;
                font-size:16px;
                font-weight:bold;
                background-color:#16a34a;
                color:white;
                border:none;
                border-radius:6px;
                cursor:pointer;
                "
                onclick="navigator.clipboard.writeText(document.getElementById('cebox').value)">
                📋 Copy CE
                </button>
                """, height=150)


            # 🔴 PE
            with col2:
                st.markdown("### 🔴 PE")

                components.html(f"""
                <textarea id="pebox" style="
                width:100%;
                height:70px;
                font-size:13px;
                padding:8px;
                box-sizing:border-box;">
                {pe_string}
                </textarea>

                <br><br>

                <button style="
                width:100%;
                height:45px;
                font-size:16px;
                font-weight:bold;
                background-color:#dc2626;
                color:white;
                border:none;
                border-radius:6px;
                cursor:pointer;
                "
                onclick="navigator.clipboard.writeText(document.getElementById('pebox').value)">
                📋 Copy PE
                </button>
                """, height=150)

        # -------- TAB 5 : AVERAGE ONLY --------
        with tab3:

            if uploaded_file and calculate and 'atm_strike' in locals():

                st.subheader("📊 Average Only (ATM ± 10 Strikes)")

                all_strikes = sorted(
                    df[df["Expiry Date"] == expiry_str]["Strike Price"].unique()
                )

                if len(all_strikes) > 0:

                    # Find ATM index
                    idx = min(range(len(all_strikes)), key=lambda i: abs(all_strikes[i] - atm_strike))

                    # Get 10 above & 10 below
                    selected_strikes = all_strikes[max(0, idx-24): idx+25]

                    avg_rows = []

                    for s in selected_strikes:

                        ce = get_price("CE", s)
                        pe = get_price("PE", s)

                        if ce is not None and pe is not None and ce > 0 and pe > 0:
                            avg = (ce + pe) / 2
                            avg_rows.append([int(s), f"{avg:.2f}"])

                    avg_df = pd.DataFrame(avg_rows, columns=["Strike", "Average"])

                    # Highlight ATM
                    def highlight_atm(row):
                        if row["Strike"] == int(atm_strike):
                            return ["background-color: yellow; color: black; font-weight: bold"] * 2
                        return [""] * 2

                    st.dataframe(avg_df.style.apply(highlight_atm, axis=1), use_container_width=True)
        # ----------- TAB 3 : SEE-SAW + RESULTS -----------
        with tab4:

            if uploaded_file and calculate:

                st.subheader("🔄 See-Saw Calculation")

                # ✅ DISPLAY TABLE
                components.html(html, height=600, scrolling=True)

                # -------- EXPORT --------
                st.subheader("📥 Export to Excel")

                export_df = mapping_df.copy()
                export_df.columns = ["Strike", "Call", "Put"]

                csv = export_df.to_csv(index=False).encode('utf-8')

                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="SeeSaw_Rules.csv",
                    mime="text/csv"
                )

                # -------- TRADINGVIEW --------
                st.subheader("📌 TradingView Pine Input")

                # 🎯 CALCULATE BEP ONLY ONCE
                bep_value = None

                if 'atm_strike' in locals():
                    ce_bep = get_price("CE", atm_strike - 100)
                    pe_bep = get_price("PE", atm_strike + 100)

                    if ce_bep is not None and pe_bep is not None:
                        bep_value = round((ce_bep + pe_bep) / 2, 2)

                # 🎯 DISPLAY BEP
                if bep_value:
                    st.markdown(f"### 🟡 BEP: {bep_value}")
                else:
                    st.markdown("### 🟡 BEP: NA")

                # -------- BUILD LISTS --------
                call_list = []
                put_list = []

                # 🟢 CALL → DESCENDING
                call_df = mapping_df.sort_values(by="Strike", ascending=False)

                for _, row in call_df.iterrows():
                    strike = int(row["Strike"] - 0)   # ✅ FIX
                    call_price = round(row["Put"], 2)
                    call_list.append(f"{strike},{call_price}")

                # 🔴 PUT → ASCENDING
                put_df = mapping_df.sort_values(by="Strike", ascending=True)

                for _, row in put_df.iterrows():
                    strike = int(row["Strike"] + 0)   # ✅ FIX
                    put_price = round(row["Call"], 2)
                    put_list.append(f"{strike},{put_price}")

                # 🎯 ADD BEP INTO BOTH LISTS (FINAL FIX)
                if bep_value is not None:
                    call_list.append(f"{int(atm_strike - 100)},{bep_value}")
                    put_list.append(f"{int(atm_strike + 100)},{bep_value}")

                # -------- STRING FORMAT --------
                call_string = "[" + ",".join(call_list) + "]"
                put_string = "[" + ",".join(put_list) + "]"

                # -------- COPY UI --------
                col1, col2 = st.columns(2)

                # 🟢 CALL
                with col1:
                    st.markdown("### 🟢 CALL")

                    components.html(f"""
                    <textarea id="callbox" style="width:100%;height:80px;">{call_string}</textarea>
                    <br>
                    <button onclick="navigator.clipboard.writeText(document.getElementById('callbox').value)">
                    Copy CALL
                    </button>
                    """, height=120)

                # 🔴 PUT
                with col2:
                    st.markdown("### 🔴 PUT")

                    components.html(f"""
                    <textarea id="putbox" style="width:100%;height:80px;">{put_string}</textarea>
                    <br>
                    <button onclick="navigator.clipboard.writeText(document.getElementById('putbox').value)">
                    Copy PUT
                    </button>
                    """, height=120)

                # -------- ATM / BEP / CHART --------
                if 'atm_strike' in locals():

                    diff = round(atm_ce - atm_pe, 2)

                    st.subheader("📍 Minimum Difference Strike (ATM)")
                    st.success(
                        f"Strike: {int(atm_strike)} | CE: {atm_ce:.2f} | PE: {atm_pe:.2f} | Diff: {diff:.2f}"
                    )

                    st.divider()

                    if bep_value is not None:
                        st.subheader("💰 BEP")
                        st.success(f"{bep_value:.2f}")

                    st.divider()

                    st.subheader("📈 Charts to be Used")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.success(f"🟢 NIFTY {expiry_str} CE {int(atm_strike - 100)}")

                    with col2:
                        st.error(f"🔴 NIFTY {expiry_str} PE {int(atm_strike + 100)}")
    

        # -------- VARIATIONS --------
        with tab5:

            if uploaded_file and calculate and 'atm_strike' in locals():

                st.subheader("📊 Variations")

                all_strikes = sorted(
                    df[df["Expiry Date"] == expiry_str]["Strike Price"].unique()
                )

                if len(all_strikes) > 0:

                    idx = min(range(len(all_strikes)), key=lambda i: abs(all_strikes[i] - atm_strike))

                    selected_strikes = all_strikes[max(0, idx-20): idx+21]

                    ce_html = """
        <style>
        .custom-table {
            width: 100%;
            border-collapse: collapse;
        }
        .custom-table th {
            background-color: #111827;
            color: white;
            padding: 8px;
        }
        .custom-table td {
            padding: 6px;
            text-align: center;
            border-bottom: 1px solid #333;
        }
        </style>

        <h4 style="color:white;">🟢 CE</h4>
        <table class="custom-table">
        <tr><th>Strike</th><th>High</th><th>Low</th></tr>
        """

                    pe_html = """
         <style>
        .custom-table {
            width: 100%;
            border-collapse: collapse;
        }
        .custom-table th {
            background-color: #111827;
            color: white;
            padding: 8px;
        }
        .custom-table td {
            padding: 6px;
            text-align: center;
            border-bottom: 1px solid #333;
        }
        </style>

        <h4 style="color:white;">🔴 PE</h4>
        <table class="custom-table">
        <tr><th>Strike</th><th>High</th><th>Low</th></tr>
        """


                    prev_ce_high = None
                    prev_ce_low = None

                    prev_pe_high = None
                    prev_pe_low = None
                
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

                        ce_high = ce_row.iloc[0]["High Price"] if not ce_row.empty and pd.notnull(ce_row.iloc[0]["High Price"]) else None
                        ce_low  = ce_row.iloc[0]["Low Price"] if not ce_row.empty and pd.notnull(ce_row.iloc[0]["Low Price"]) else None

                        pe_high = pe_row.iloc[0]["High Price"] if not pe_row.empty and pd.notnull(pe_row.iloc[0]["High Price"]) else None
                        pe_low  = pe_row.iloc[0]["Low Price"] if not pe_row.empty and pd.notnull(pe_row.iloc[0]["Low Price"]) else None

                        # ---------------- CE LOGIC ----------------
                        ce_bg = ""
                        ce_text = "white"

                        # CE DESCENDING CHECK
                        if prev_ce_high is not None and ce_high is not None:
                            if ce_high > prev_ce_high:
                                ce_bg = "#ff4d4d"; ce_text = "white"

                        if prev_ce_low is not None and ce_low is not None:
                            if ce_low > prev_ce_low:
                                ce_bg = "#ff4d4d"; ce_text = "white"
    
                        ce_html += f"""
                        <tr style="background-color:{ce_bg}; color:{ce_text}; font-weight:bold;">
                        <td>{int(s)}</td>
                        <td>{f"{ce_high:.2f}" if pd.notnull(ce_high) else ""}</td>
                        <td>{f"{ce_low:.2f}" if pd.notnull(ce_low) else ""}</td>
                        </tr>
                        """

                        if ce_high is not None:
                            prev_ce_high = ce_high
                        if ce_low is not None:
                            prev_ce_low = ce_low

                        # ---------------- PE LOGIC ----------------
                        pe_bg = ""
                        pe_text = "white"
                   
                        # PE ASCENDING CHECK
                        if prev_pe_high is not None and pe_high is not None:
                            if pe_high < prev_pe_high:
                                pe_bg = "#ff4d4d"; pe_text = "white"

                        if prev_pe_low is not None and pe_low is not None:
                            if pe_low < prev_pe_low:
                                pe_bg = "#ff4d4d"; pe_text = "white"

                        pe_html += f"""
                        <tr style="background-color:{pe_bg}; color:{pe_text}; font-weight:bold;">
                        <td>{int(s)}</td>
                        <td>{f"{pe_high:.2f}" if pd.notnull(pe_high) else ""}</td>
                        <td>{f"{pe_low:.2f}" if pd.notnull(pe_low) else ""}</td>
                        </tr>
                        """

                        if pe_high is not None:
                            prev_pe_high = pe_high
                        if pe_low is not None:
                            prev_pe_low = pe_low                

                    ce_html += "</table>"
                    pe_html += "</table>"

                    # DISPLAY SIDE BY SIDE
                    col1, col2 = st.columns(2)

                    with col1:
                        components.html(ce_html, height=500, scrolling=True)

                    with col2:
                        components.html(pe_html, height=500, scrolling=True)
