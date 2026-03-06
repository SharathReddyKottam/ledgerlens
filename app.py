import hashlib
import streamlit as st
import plotly.express as px
import pandas as pd
from utils.parser_router import extract_transactions


st.set_page_config(page_title="LedgerLens", layout="wide")

st.title("LedgerLens")
st.caption(
    "Upload one or more credit card or bank statement PDFs to extract, normalize, and analyze transactions."
)


def build_statement_fingerprint(df: pd.DataFrame, bank: str):
    """Create a fingerprint for an uploaded statement to detect duplicate statements."""
    if df is None or df.empty:
        return None

    first_date = str(df["date"].min().date())
    last_date = str(df["date"].max().date())
    total_rows = str(len(df))
    total_amount = f"{df['amount'].sum():.2f}"

    sample_descriptions = "|".join(
        df["description"].astype(str).head(5).tolist()
    )

    raw_key = f"{bank}|{first_date}|{last_date}|{total_rows}|{total_amount}|{sample_descriptions}"
    return hashlib.md5(raw_key.encode()).hexdigest()


st.sidebar.header("Controls")
debug_mode = st.sidebar.checkbox("Debug mode", value=False)

uploaded_files = st.file_uploader(
    "Upload statement PDF(s)",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    all_dfs = []
    file_results = []
    debug_results = []
    seen_statement_fingerprints = set()

    for uploaded_file in uploaded_files:
        result = extract_transactions(uploaded_file)

        bank = result["bank"]
        parser_name = result["parser"]
        confidence = result["confidence"]
        raw_rows = result["raw_rows"]
        df = result["clean_df"]

        if bank == "unknown":
            file_results.append(
                {
                    "file_name": uploaded_file.name,
                    "bank": "UNKNOWN",
                    "parser": parser_name,
                    "confidence": confidence,
                    "status": "Unsupported format",
                    "rows": 0,
                }
            )

            debug_results.append(
                {
                    "file_name": uploaded_file.name,
                    "bank": "UNKNOWN",
                    "parser": parser_name,
                    "confidence": confidence,
                    "raw_rows": raw_rows,
                    "clean_df": df,
                }
            )
            continue

        if df is None or df.empty:
            file_results.append(
                {
                    "file_name": uploaded_file.name,
                    "bank": bank.upper(),
                    "parser": parser_name,
                    "confidence": confidence,
                    "status": "No transactions extracted",
                    "rows": 0,
                }
            )

            debug_results.append(
                {
                    "file_name": uploaded_file.name,
                    "bank": bank.upper(),
                    "parser": parser_name,
                    "confidence": confidence,
                    "raw_rows": raw_rows,
                    "clean_df": df,
                }
            )
            continue

        fingerprint = build_statement_fingerprint(df, bank)

        if fingerprint in seen_statement_fingerprints:
            file_results.append(
                {
                    "file_name": uploaded_file.name,
                    "bank": bank.upper(),
                    "parser": parser_name,
                    "confidence": confidence,
                    "status": "Duplicate statement skipped",
                    "rows": 0,
                }
            )

            debug_results.append(
                {
                    "file_name": uploaded_file.name,
                    "bank": bank.upper(),
                    "parser": parser_name,
                    "confidence": confidence,
                    "raw_rows": raw_rows,
                    "clean_df": df,
                }
            )
            continue

        seen_statement_fingerprints.add(fingerprint)

        df = df.copy()
        df["source_file"] = uploaded_file.name
        all_dfs.append(df)

        file_results.append(
            {
                "file_name": uploaded_file.name,
                "bank": bank.upper(),
                "parser": parser_name,
                "confidence": confidence,
                "status": "Parsed successfully",
                "rows": len(df),
            }
        )

        debug_results.append(
            {
                "file_name": uploaded_file.name,
                "bank": bank.upper(),
                "parser": parser_name,
                "confidence": confidence,
                "raw_rows": raw_rows,
                "clean_df": df,
            }
        )

    st.subheader("Upload Summary")
    summary_df = pd.DataFrame(file_results)
    st.dataframe(summary_df, use_container_width=True)

    if debug_mode:
        st.subheader("Debug Preview")

        for item in debug_results:
            with st.expander(
                    f"{item['file_name']} | {item['bank']} | {item['parser']} | Confidence: {item['confidence']}"
            ):
                st.write(f"**Detected bank:** {item['bank']}")
                st.write(f"**Parser used:** {item['parser']}")
                st.write(f"**Parser confidence:** {item['confidence']}")

                st.write("### Raw Matched Rows")
                if item["raw_rows"] is not None and not item["raw_rows"].empty:
                    st.dataframe(item["raw_rows"], use_container_width=True)
                else:
                    st.info("No raw rows matched.")

                st.write("### Cleaned Rows")
                if item["clean_df"] is not None and not item["clean_df"].empty:
                    st.dataframe(item["clean_df"], use_container_width=True)
                else:
                    st.info("No cleaned rows produced.")

    if not all_dfs:
        st.warning("No supported statements were successfully parsed.")
        st.stop()

    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df = combined_df.sort_values("date").reset_index(drop=True)

    # Remove duplicate transactions across uploaded statements
    combined_df = combined_df.drop_duplicates(
        subset=["date", "description", "amount", "bank"],
        keep="first"
    ).reset_index(drop=True)

    st.success(
        f"Combined {len(combined_df)} transactions from {combined_df['source_file'].nunique()} unique statement file(s)"
    )

    st.sidebar.header("Filters")

    min_date = combined_df["date"].min().date()
    max_date = combined_df["date"].max().date()

    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    bank_options = sorted(combined_df["bank"].dropna().unique().tolist())
    selected_banks = st.sidebar.multiselect(
        "Bank",
        options=bank_options,
        default=bank_options,
    )

    category_options = sorted(combined_df["category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Category",
        options=category_options,
        default=category_options,
    )

    merchant_search = st.sidebar.text_input("Search merchant / description")

    filtered_df = combined_df.copy()

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["date"].dt.date >= start_date) &
            (filtered_df["date"].dt.date <= end_date)
            ]

    if selected_banks:
        filtered_df = filtered_df[filtered_df["bank"].isin(selected_banks)]

    if selected_categories:
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]

    if merchant_search.strip():
        filtered_df = filtered_df[
            filtered_df["description"].str.contains(
                merchant_search.strip(),
                case=False,
                na=False
            )
        ]

    if filtered_df.empty:
        st.warning("No transactions match the selected filters.")
        st.stop()

    outflow_df = filtered_df[filtered_df["amount"] > 0].copy()
    inflow_df = filtered_df[filtered_df["amount"] < 0].copy()

    total_outflow = outflow_df["amount"].sum()
    total_inflow = inflow_df["amount"].sum()
    net_total = filtered_df["amount"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Outflows / Spend", f"${total_outflow:.2f}")
    c2.metric("Total Inflows / Payments", f"${total_inflow:.2f}")
    c3.metric("Net Total", f"${net_total:.2f}")
    c4.metric("Transactions", f"{len(filtered_df)}")

    all_csv = combined_df.to_csv(index=False).encode("utf-8")
    filtered_csv = filtered_df.to_csv(index=False).encode("utf-8")

    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "Download all parsed transactions (CSV)",
            data=all_csv,
            file_name="all_parsed_transactions.csv",
            mime="text/csv",
        )
    with d2:
        st.download_button(
            "Download filtered transactions (CSV)",
            data=filtered_csv,
            file_name="filtered_transactions.csv",
            mime="text/csv",
        )

    st.subheader("Statement Summary")
    statement_summary = (
        filtered_df.groupby(["source_file", "bank"], as_index=False)
        .agg(
            transactions=("amount", "count"),
            total_outflows=("amount", lambda s: s[s > 0].sum()),
            total_inflows=("amount", lambda s: s[s < 0].sum()),
            net_total=("amount", "sum"),
        )
    )
    st.dataframe(statement_summary, use_container_width=True)

    st.subheader("Transactions")
    display_cols = ["date", "description", "category", "amount", "bank", "source_file"]
    if "account_type" in filtered_df.columns:
        display_cols.insert(4, "account_type")

    st.dataframe(filtered_df[display_cols], use_container_width=True)

    monthly = (
        outflow_df.assign(month=outflow_df["date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)["amount"]
        .sum()
    )

    st.subheader("Monthly Outflows / Spending")
    fig_monthly = px.bar(
        monthly,
        x="month",
        y="amount",
        title="Monthly Outflows / Spending",
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

    merchants = (
        outflow_df.groupby("description", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        .head(10)
    )

    st.subheader("Top Merchants / Payees")
    fig_merchants = px.bar(
        merchants,
        x="amount",
        y="description",
        orientation="h",
        title="Top Merchants / Payees",
    )
    fig_merchants.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_merchants, use_container_width=True)

    category_df = (
        outflow_df.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )

    st.subheader("Outflows / Spending by Category")
    fig_category = px.pie(
        category_df,
        names="category",
        values="amount",
        title="Category Distribution",
    )
    st.plotly_chart(fig_category, use_container_width=True)

    bank_compare = (
        outflow_df.groupby("bank", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )

    st.subheader("Bank-wise Outflow Comparison")
    fig_bank = px.bar(
        bank_compare,
        x="bank",
        y="amount",
        title="Outflows by Bank",
    )
    st.plotly_chart(fig_bank, use_container_width=True)

    st.subheader("Quick Insights")

    top_category = category_df.iloc[0]["category"] if not category_df.empty else "N/A"
    top_category_amount = category_df.iloc[0]["amount"] if not category_df.empty else 0
    largest_txn = outflow_df["amount"].max() if not outflow_df.empty else 0
    largest_txn_merchant = (
        outflow_df.loc[outflow_df["amount"].idxmax(), "description"]
        if not outflow_df.empty else "N/A"
    )
    avg_outflow = outflow_df["amount"].mean() if not outflow_df.empty else 0

    st.write(f"• Biggest category: **{top_category}** (${top_category_amount:.2f})")
    st.write(f"• Average outflow amount: **${avg_outflow:.2f}**")
    st.write(f"• Largest outflow: **${largest_txn:.2f}** at **{largest_txn_merchant}**")
    st.write(f"• Number of inflow/payment transactions: **{len(inflow_df)}**")
    st.write(f"• Number of outflow/spending transactions: **{len(outflow_df)}**")

else:
    st.info("Upload one or more PDF statements to start analysis.")