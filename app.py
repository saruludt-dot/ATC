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

# -------- LOGO --------
def get_img(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

col_logo, col_tabs, col_logout = st.columns([2.5,6.25,1.25])

with col_logout:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

with col_logo:
    logo = get_img("logo.png")
    st.markdown(f"<img src='data:image/png;base64,{logo}' width='300%'>", unsafe_allow_html=True)

# -------- TABS --------
with col_tabs:
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Input",
        "📊 16 Rules",
        "📊 Average + Completion",
        "🔄 See-Saw"
    ])

# -------- INPUT --------
with tab1:
    yesterday_file = st.file_uploader("Upload Yesterday CSV")
    today_file = st.file_uploader("Upload Today CSV")
    expiry = st.date_input("Expiry Date")
    calculate = st.button("Calculate")

# -------- MAIN --------
if yesterday_file and today_file and calculate:

    try:
        df_y = pd.read_csv(yesterday_file, on_bad_lines='skip', engine='python')
        df_t = pd.read_csv(today_file, on_bad_lines='skip', engine='python')

        # -------- CLEAN --------
        def clean(df):
            df.columns = df.columns.str.strip()
            df["Expiry Date"] = df["Expiry Date"].astype(str).str.strip()
            df["Option Type"] = df["Option Type"].str.strip().str.upper()
            df["Strike Price"] = df["Strike Price"].astype(str).str.replace(",", "").astype(float)
            df["Close Price"] = pd.to_numeric(df["Close Price"], errors="coerce")
            df["High Price"] = pd.to_numeric(df["High Price"], errors="coerce")
            df["Low Price"] = pd.to_numeric(df["Low Price"], errors="coerce")
            return df

        df_y = clean(df_y)
        df_t = clean(df_t)

        expiry_str = expiry.strftime("%d-%b-%Y")

        # -------- GET PRICE --------
        def get_price(data, opt, s):
            r = data[
                (data["Expiry Date"]==expiry_str) &
                (data["Option Type"]==opt) &
                (data["Strike Price"]==s)
            ]
            return r.iloc[0]["Close Price"] if not r.empty else None

        strikes = sorted(df_y[df_y["Expiry Date"]==expiry_str]["Strike Price"].unique())

        # -------- AVERAGE --------
        avg_rows = []

        for s in strikes:
            ce = get_price(df_y, "CE", s)
            pe = get_price(df_y, "PE", s)

            if ce and pe:
                avg_rows.append([int(s), round((ce+pe)/2,2)])

        avg_df = pd.DataFrame(avg_rows, columns=["Strike", "Average"])

        # -------- TAB 3 --------
        with tab3:

            st.subheader("📊 Average")
            st.dataframe(avg_df, use_container_width=True)

            st.subheader("✅ Completion Check")

            df_t = df_t[df_t["Expiry Date"] == expiry_str]

            result = []

            for _, row in avg_df.iterrows():

                s = row["Strike"]
                avg = row["Average"]

                ce = df_t[(df_t["Option Type"]=="CE") & (df_t["Strike Price"]==s)]
                pe = df_t[(df_t["Option Type"]=="PE") & (df_t["Strike Price"]==s)]

                ce_low = ce_high = pe_low = pe_high = None

                if not ce.empty:
                    ce_low = ce.iloc[0]["Low Price"]
                    ce_high = ce.iloc[0]["High Price"]

                if not pe.empty:
                    pe_low = pe.iloc[0]["Low Price"]
                    pe_high = pe.iloc[0]["High Price"]

                def check(a, low, high):
                    if low is None or high is None:
                        return ""
                    return "✅" if min(low, high) <= a <= max(low, high) else "❌"

                result.append([
                    s, avg,
                    ce_low, ce_high,
                    pe_low, pe_high,
                    check(avg, ce_low, ce_high),
                    check(avg, pe_low, pe_high)
                ])

            res_df = pd.DataFrame(result, columns=[
                "Strike","Avg",
                "CE Low","CE High",
                "PE Low","PE High",
                "CE ✔","PE ✔"
            ])

            res_df = res_df.fillna("")

            def highlight(row):
                styles = [""] * len(row)
                if row["CE ✔"] == "✅":
                    styles[6] = "background-color:#d4edda"
                if row["CE ✔"] == "❌":
                    styles[6] = "background-color:#f8d7da"
                if row["PE ✔"] == "✅":
                    styles[7] = "background-color:#d4edda"
                if row["PE ✔"] == "❌":
                    styles[7] = "background-color:#f8d7da"
                return styles

            st.dataframe(res_df.style.apply(highlight, axis=1), use_container_width=True)

        # -------- TAB 4 SEE-SAW --------
        with tab4:

            st.subheader("🔄 See-Saw View")

            mapping = []

            for s in strikes:
                pe = get_price(df_y, "PE", s + 100)
                ce = get_price(df_y, "CE", s - 100)

                if pe is not None and ce is not None:
                    mapping.append([int(s), ce, pe])

            mapping_df = pd.DataFrame(mapping, columns=["Strike", "Call", "Put"])

            html = "<table border='1' style='width:100%;text-align:center'>"
            html += "<tr><th>Strike</th><th>Call</th><th>Strike</th><th>Put</th></tr>"

            for i in range(len(mapping_df)):
                left = mapping_df.iloc[len(mapping_df)-1-i]
                right = mapping_df.iloc[i]

                html += f"""
                <tr>
                <td>{int(left['Strike'])}</td>
                <td>{left['Put']:.2f}</td>
                <td>{int(right['Strike'])}</td>
                <td>{right['Call']:.2f}</td>
                </tr>
                """

            html += "</table>"

            components.html(html, height=500, scrolling=True)

    except Exception as e:
        st.error(f"Error: {e}")
