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
