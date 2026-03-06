import re
import pandas as pd
import pdfplumber
from utils.common import to_fileobj, finalize_dataframe


def extract_applecard_transactions(pdf_file):
    fileobj = to_fileobj(pdf_file)

    payment_rows = []
    transaction_rows = []

    # Apple Card rows look like:
    # 02/27/2026 ACH Deposit Internet transfer from account ending in 0735 -$17.99
    payment_pattern = re.compile(
        r"^(?P<date>\d{2}/\d{2}/\d{4})\s+(?P<description>.+?)\s+(?P<amount>-?\$?\d+(?:,\d{3})*\.\d{2}|-\$\d+(?:,\d{3})*\.\d{2})$"
    )

    # Apple Card transaction rows look like:
    # 02/02/2026 SQ *FOUNDATION COFFEE ... 2% $0.25 $12.65
    # We want the final amount, not Daily Cash
    transaction_pattern = re.compile(
        r"^(?P<date>\d{2}/\d{2}/\d{4})\s+(?P<description>.+?)\s+\d+%\s+\$?\d+(?:,\d{3})*\.\d{2}\s+(?P<amount>\$?\d+(?:,\d{3})*\.\d{2})$"
    )

    with pdfplumber.open(fileobj) as pdf:
        section = None

        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            for raw_line in text.splitlines():
                line = re.sub(r"\s+", " ", raw_line).strip()
                upper_line = line.upper()

                if upper_line == "PAYMENTS":
                    section = "payments"
                    continue

                if upper_line == "TRANSACTIONS":
                    section = "transactions"
                    continue

                if upper_line.startswith("INTEREST CHARGED"):
                    section = None
                    continue

                if section == "payments":
                    match = payment_pattern.match(line)
                    if match:
                        payment_rows.append(
                            {
                                "page": page_num,
                                "date": match.group("date"),
                                "description": match.group("description"),
                                "amount": match.group("amount"),
                                "matched_line": line,
                            }
                        )

                elif section == "transactions":
                    match = transaction_pattern.match(line)
                    if match:
                        transaction_rows.append(
                            {
                                "page": page_num,
                                "date": match.group("date"),
                                "description": match.group("description"),
                                "amount": match.group("amount"),
                                "matched_line": line,
                            }
                        )

    raw_df = pd.DataFrame(payment_rows + transaction_rows)

    clean_df = finalize_dataframe(
        raw_df[["date", "description", "amount"]].copy() if not raw_df.empty else pd.DataFrame(),
        bank_name="APPLE CARD",
        date_format="%m/%d/%Y",
        invert_sign=False,
        account_type="credit",
    )

    confidence = "High" if len(raw_df) >= 2 else "Medium" if len(raw_df) > 0 else "Low"

    return {
        "bank": "applecard",
        "parser": "Apple Card Parser",
        "confidence": confidence,
        "raw_rows": raw_df,
        "clean_df": clean_df,
    }