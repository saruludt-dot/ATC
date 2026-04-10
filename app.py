import streamlit as st
import pandas as pd
import base64
import streamlit.components.v1 as components

# ---------------- SESSION ----------------
if "calculated" not in st.session_state:
    st.session_state.calculated = False

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
# 📈 CALCULATIONS (OLD + FIXED)
# =====================================================
if page == "📈 Calculations":

    st.markdown("<h1>📈 Dashboard</h1><hr>", unsafe_allow_html=True)

    # -------- INPUT (NO TABS INITIALLY) --------
    col1, col2, col3 = st.columns(3)

    with col1:
        uploaded_file = st.file_uploader("📥 Upload CSV")

    with col2:
        expiry = st.date_input("📅 Expiry Date")

    with col3:
        strike = st.number_input("🎯 Strike", step=50)

    if st.button("🚀 Calculate", use_container_width=True):
        st.session_state.calculated = True

    # -------- MAIN LOGIC --------
    if uploaded_file and st.session_state.calculated:

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
            if ce is not None and pe is not None:
                diff_list.append((s, abs(ce-pe)))

        atm_strike = min(diff_list, key=lambda x: x[1])[0]

        # -------- SHOW TABS AFTER CLICK --------
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 16 Rules",
            "📊 Average Only",
            "🔄 See-Saw",
            "📊 Variations",
            "📍 Info"
        ])

        # ================= 16 RULES =================
        with tab1:

            rows = []

            ce = get_price("CE", strike)
            pe = get_price("PE", strike)

            if ce is not None and pe is not None:
                val = (ce+pe)/2
                rows.append(["A", f"{val:.2f}", "A", f"{val:.2f}"])

            ce = get_price("CE", strike+100)
            pe = get_price("PE", strike-100)

            if ce is not None and pe is not None:
                val = (ce+pe)/2
                rows.append(["B", f"{val:.2f}", "B", f"{val:.2f}"])

            table_df = pd.DataFrame(rows, columns=["Name","CE","Name ","PE"])
            st.dataframe(table_df)

        # ================= AVERAGE (±12) =================
        with tab2:

            all_strikes = sorted(
                df[df["Expiry Date"] == expiry_str]["Strike Price"].unique()
            )

            idx = min(range(len(all_strikes)), key=lambda i: abs(all_strikes[i] - atm_strike))

            selected_strikes = all_strikes[max(0, idx-12): idx+13]

            avg_rows = []

            for s in selected_strikes:
                ce = get_price("CE", s)
                pe = get_price("PE", s)

                if ce is not None and pe is not None:
                    avg = (ce + pe) / 2
                    avg_rows.append([int(s), f"{avg:.2f}"])

            avg_df = pd.DataFrame(avg_rows, columns=["Strike", "Average"])

            def highlight(row):
                if row["Strike"] == int(atm_strike):
                    return ["background-color: yellow; color:black"]*2
                return [""]*2

            st.dataframe(avg_df.style.apply(highlight, axis=1))

        # ================= SEE-SAW =================
        with tab3:

            mapping = []

            for s in sorted(strikes):
                pe = get_price("PE", s + 100)
                ce = get_price("CE", s - 100)

                if pe is not None and ce is not None:
                    mapping.append([int(s), ce, pe])

            mapping_df = pd.DataFrame(mapping, columns=["Strike","Call","Put"])
            st.dataframe(mapping_df)

        # ================= VARIATIONS =================
        with tab4:

            rows = []

            for s in sorted(strikes):

                ce_row = df[(df["Option Type"]=="CE") & (df["Strike Price"]==s)]
                pe_row = df[(df["Option Type"]=="PE") & (df["Strike Price"]==s)]

                ce_high = ce_row.iloc[0]["High Price"] if not ce_row.empty else None
                pe_high = pe_row.iloc[0]["High Price"] if not pe_row.empty else None

                rows.append([int(s), ce_high, pe_high])

            df_var = pd.DataFrame(rows, columns=["Strike","CE High","PE High"])
            st.dataframe(df_var)

        # ================= INFO =================
        with tab5:
            st.success(f"ATM Strike: {int(atm_strike)}")

# =====================================================
# 📊 STRIKES SOLD (KEEP YOUR OLD)
# =====================================================
elif page == "📊 Strikes Sold":
    st.info("Use your working Strikes Sold code here")
