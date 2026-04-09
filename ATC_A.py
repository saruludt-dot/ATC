import streamlit as st
import pandas as pd

st.title("📊 Options Value Tracker")

# Upload files
input_file = st.file_uploader("Upload Values Excel", type=["xlsx"])
mw_file = st.file_uploader("Upload MW File", type=["csv"])

if input_file and mw_file:

    # =========================
    # ✅ STEP 1: READ INPUT FILE
    # =========================
    df_input = pd.read_excel(input_file)

    # Remove extra column (if exists)
    df_input = df_input.loc[:, df_input.columns != 0]

    # Clean column names
    df_input.columns = df_input.columns.str.strip().str.lower()

    # Convert strike
    df_input["strike"] = df_input["strike"].astype(float)

    #st.write("Input Columns:", df_input.columns)

    # =========================
    # ✅ STEP 2: READ MW FILE
    # =========================
    df_mw = pd.read_csv(mw_file)

    # Clean column names
    df_mw.columns = df_mw.columns.str.strip().str.upper()

    #st.write("MW Columns:", df_mw.columns)

    # =========================
    # ✅ STEP 3: CLEAN MW DATA
    # =========================

    # Clean STRIKE
    df_mw["STRIKE"] = (
        df_mw["STRIKE"]
        .astype(str)
        .str.replace(",", "")
        .astype(float)
    )

    # Clean LOW / HIGH
    df_mw["LOW"] = df_mw["LOW"].astype(str).str.replace(",", "").astype(float)
    df_mw["HIGH"] = df_mw["HIGH"].astype(str).str.replace(",", "").astype(float)

    # Convert CALL/PUT → CE/PE
    df_mw["OPTION TYPE"] = df_mw["OPTION TYPE"].astype(str).str.strip().replace({
        "Call": "CE",
        "Put": "PE",
        "CALL": "CE",
        "PUT": "PE"
    })

    # Filter only NIFTY (important)
    df_mw = df_mw[df_mw["SYMBOL"] == "NIFTY"]

    # =========================
    # ✅ STEP 4: PROCESS
    # =========================
    results = []

    for _, row in df_input.iterrows():

        strike = row["strike"]
        value = row["value to check"]

        # ---- CE ----
        ce = df_mw[
            (df_mw["OPTION TYPE"] == "CE") &
            (abs(df_mw["STRIKE"] - strike) < 1)
        ]

        ce_low = ce_high = None
        ce_status = "❌ Not Completed"

        if not ce.empty:
            ce_low = ce.iloc[0]["LOW"]
            ce_high = ce.iloc[0]["HIGH"]

            if ce_low <= value <= ce_high:
                ce_status = "✅ Completed"

        # ---- PE ----
        pe = df_mw[
            (df_mw["OPTION TYPE"] == "PE") &
            (abs(df_mw["STRIKE"] - strike) < 1)
        ]

        pe_low = pe_high = None
        pe_status = "❌ Not Completed"

        if not pe.empty:
            pe_low = pe.iloc[0]["LOW"]
            pe_high = pe.iloc[0]["HIGH"]

            if pe_low <= value <= pe_high:
                pe_status = "✅ Completed"

        results.append({
            "Strike": strike,
            "Value to check": value,
            "CE Low": ce_low,
            "CE High": ce_high,
            "PE Low": pe_low,
            "PE High": pe_high,
            "CE Status": ce_status,
            "PE Status": pe_status
        })

    # =========================
    # ✅ STEP 5: DISPLAY
    # =========================
    result_df = pd.DataFrame(results)

    st.dataframe(result_df, use_container_width=True)