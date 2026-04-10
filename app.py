import streamlit as st
import pandas as pd

# ---------------- SESSION STATE INIT ----------------
if "calculated" not in st.session_state:
    st.session_state.calculated = False

if "atm_strike" not in st.session_state:
    st.session_state.atm_strike = None

# ---------------- UI HEADER ----------------
st.title("📊 AADHITH TRADING CORPORATION")
st.markdown("---")

# ---------------- INPUT SECTION ----------------
col1, col2, col3 = st.columns(3)

with col1:
    uploaded_file = st.file_uploader("📥 Upload CSV")

with col2:
    expiry = st.date_input("📅 Expiry Date")

with col3:
    strike = st.number_input("🎯 Strike", step=50)

# ---------------- CALCULATE BUTTON ----------------
if st.button("🚀 Calculate", use_container_width=True):
    st.session_state.calculated = True

# ---------------- MAIN LOGIC ----------------
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
        r = df[(df["Expiry Date"] == expiry_str) &
               (df["Option Type"] == opt) &
               (df["Strike Price"] == s)]
        return r.iloc[0]["Close Price"] if not r.empty else None

    # ---------------- ATM CALCULATION ----------------
    diff_list = []
    strikes = df[df["Expiry Date"] == expiry_str]["Strike Price"].unique()

    for s in strikes:
        ce = get_price("CE", s)
        pe = get_price("PE", s)

        if ce and pe and 10 < ce < 1000 and 10 < pe < 1000:
            diff_list.append((s, ce, pe, abs(ce - pe)))

    if diff_list:
        atm_strike, atm_ce, atm_pe, _ = min(diff_list, key=lambda x: x[3])
        st.session_state.atm_strike = atm_strike

    # ---------------- SHOW TABS ----------------
    if st.session_state.atm_strike is not None:

        tab1, tab2, tab3 = st.tabs([
            "📊 16 Rules",
            "📊 Average",
            "📍 ATM Info"
        ])

        # ---------------- TAB 1 ----------------
        with tab1:
            rows = []

            ce = get_price("CE", strike)
            pe = get_price("PE", strike)

            if ce and pe:
                val = (ce + pe) / 2
                rows.append([strike, round(val, 2)])

            df_out = pd.DataFrame(rows, columns=["Strike", "Average"])
            df_out = df_out.sort_values(by="Strike")

            st.dataframe(df_out, use_container_width=True)

        # ---------------- TAB 2 ----------------
        with tab2:
            avg_rows = []

            all_strikes = sorted(strikes)

            for s in all_strikes:
                ce = get_price("CE", s)
                pe = get_price("PE", s)

                if ce and pe:
                    avg_rows.append([int(s), round((ce + pe) / 2, 2)])

            avg_df = pd.DataFrame(avg_rows, columns=["Strike", "Average"])
            avg_df = avg_df.sort_values(by="Strike")

            def highlight(row):
                if row["Strike"] == int(st.session_state.atm_strike):
                    return ["background-color: yellow"] * 2
                return [""] * 2

            st.dataframe(avg_df.style.apply(highlight, axis=1), use_container_width=True)

        # ---------------- TAB 3 ----------------
        with tab3:
            st.success(f"ATM Strike: {int(st.session_state.atm_strike)}")

# ---------------- RESET BUTTON ----------------
if st.button("🔄 Reset"):
    st.session_state.calculated = False
    st.session_state.atm_strike = None
