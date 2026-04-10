import streamlit as st
import pandas as pd
import base64
import streamlit.components.v1 as components

# ---------------- SESSION STATE ----------------
if "calculated" not in st.session_state:
    st.session_state.calculated = False
if "atm_strike" not in st.session_state:
    st.session_state.atm_strike = None

# ---------------- IMAGE ----------------
def get_img(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Sidebar
try:
    logo = get_img("logo.png")
    st.sidebar.markdown(f"<img src='data:image/png;base64,{logo}' width='100%'>", unsafe_allow_html=True)
except Exception:
    pass

page = st.sidebar.radio("Navigation", ["📈 Calculations", "📊 Strikes Sold"])

# =====================================================
# 📈 CALCULATIONS (FULL - FIXED)
# =====================================================
if page == "📈 Calculations":

    st.title("📊 Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        uploaded_file = st.file_uploader("📥 Upload CSV")
    with col2:
        expiry = st.date_input("📅 Expiry Date")
    with col3:
        strike = st.number_input("🎯 Strike", step=50)

    if st.button("🚀 Calculate", use_container_width=True):
        st.session_state.calculated = True

    if uploaded_file and st.session_state.calculated:

        df = pd.read_csv(uploaded_file, on_bad_lines='skip', engine='python')
        df.columns = df.columns.str.strip()

        # Clean columns
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

        # ---------------- ATM ----------------
        strikes = sorted(df[df["Expiry Date"] == expiry_str]["Strike Price"].dropna().unique())

        if len(strikes) == 0:
            st.error("No strikes found for selected expiry")
            st.stop()

        diff_list = []
        for s in strikes:
            ce = get_price("CE", s)
            pe = get_price("PE", s)
            if ce is not None and pe is not None:
                diff_list.append((s, abs(ce - pe)))

        if len(diff_list) == 0:
            st.error("No CE/PE pairs found")
            st.stop()

        st.session_state.atm_strike = min(diff_list, key=lambda x: x[1])[0]

        # ---------------- TABS ----------------
        if st.session_state.atm_strike is not None:

            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 16 Rules",
                "📊 Average",
                "🔄 See-Saw",
                "📊 Variations"
            ])

            # ================= 16 RULES =================
            with tab1:
                rows = []

                # ATM
                ce = get_price("CE", strike)
                pe = get_price("PE", strike)
                if ce is not None and pe is not None:
                    rows.append(["ATM", round((ce + pe) / 2, 2)])

                # Steps
                for step in [50, 100, 150, 200]:
                    ce = get_price("CE", strike + step)
                    pe = get_price("PE", strike - step)
                    if ce is not None and pe is not None:
                        rows.append([f"±{step}", round((ce + pe) / 2, 2)])

                df_rules = pd.DataFrame(rows, columns=["Rule", "Average"])
                st.dataframe(df_rules, use_container_width=True)

            # ================= AVERAGE (±12) =================
            with tab2:
                idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - st.session_state.atm_strike))
                selected = strikes[max(0, idx - 12): idx + 13]

                avg_rows = []
                for s in selected:
                    ce = get_price("CE", s)
                    pe = get_price("PE", s)
                    if ce is not None and pe is not None:
                        avg_rows.append([int(s), round((ce + pe) / 2, 2)])

                df_avg = pd.DataFrame(avg_rows, columns=["Strike", "Average"])

                def highlight(row):
                    if row["Strike"] == int(st.session_state.atm_strike):
                        return ["background-color: yellow; color:black"] * 2
                    return [""] * 2

                st.dataframe(df_avg.style.apply(highlight, axis=1), use_container_width=True)

            # ================= SEE-SAW =================
            with tab3:
                mapping = []
                for s in strikes:
                    ce = get_price("CE", s - 100)
                    pe = get_price("PE", s + 100)
                    if ce is not None and pe is not None:
                        mapping.append([int(s), round(ce, 2), round(pe, 2)])

                df_map = pd.DataFrame(mapping, columns=["Strike", "Call", "Put"]).sort_values(by="Strike")
                st.dataframe(df_map, use_container_width=True)

                csv = df_map.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download See-Saw CSV", data=csv, file_name="seesaw.csv")

            # ================= VARIATIONS =================
            with tab4:
                var_rows = []
                for s in strikes:
                    ce_row = df[(df["Option Type"] == "CE") & (df["Strike Price"] == s)]
                    pe_row = df[(df["Option Type"] == "PE") & (df["Strike Price"] == s)]

                    ce_high = ce_row.iloc[0]["High Price"] if not ce_row.empty else None
                    pe_high = pe_row.iloc[0]["High Price"] if not pe_row.empty else None

                    var_rows.append([int(s), ce_high, pe_high])

                df_var = pd.DataFrame(var_rows, columns=["Strike", "CE High", "PE High"])
                st.dataframe(df_var, use_container_width=True)

    if st.button("🔄 Reset"):
        st.session_state.calculated = False
        st.session_state.atm_strike = None

# =====================================================
# 📊 STRIKES SOLD (placeholder - keep your working one)
# =====================================================
elif page == "📊 Strikes Sold":
    st.title("📈 Strikes Sold Today")
    st.info("Use your working Strikes Sold code here (already stable)")
