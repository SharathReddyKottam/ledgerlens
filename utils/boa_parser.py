import re
import pandas as pd
import pdfplumber
from utils.common import to_fileobj, finalize_dataframe


def extract_boa_transactions(pdf_file):
    fileobj = to_fileobj(pdf_file)
    rows = []

    pattern = re.compile(
        r"^(?P<date>\d{2}/\d{2})"
        r"\s+\d{2}/\d{2}"
        r"\s+(?P<description>.+?)"
        r"\s+\d{3,}"
        r"\s+\d{4}"
        r"\s+(?P<amount>-?\$?\d+(?:,\d{3})*\.\d{2})$"
    )

    with pdfplumber.open(fileobj) as pdf:
        in_transactions_section = False

        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            for raw_line in text.splitlines():
                line = re.sub(r"\s+", " ", raw_line).strip()
                upper_line = line.upper()

                if upper_line == "TRANSACTIONS":
                    in_transactions_section = True
                    continue

                if not in_transactions_section:
                    continue

                if upper_line.startswith("INTEREST CHARGED") or upper_line.startswith("TOTAL FEES CHARGED"):
                    break

                match = pattern.match(line)
                if match:
                    rows.append(
                        {
                            "page": page_num,
                            "date": f"{match.group('date')}/26",
                            "description": match.group("description"),
                            "amount": match.group("amount"),
                            "matched_line": line,
                        }
                    )

    raw_df = pd.DataFrame(rows)

    clean_df = finalize_dataframe(
        raw_df[["date", "description", "amount"]].copy() if not raw_df.empty else pd.DataFrame(),
        bank_name="BOA",
        date_format="%m/%d/%y",
        invert_sign=False,
        account_type="credit",
    )

    confidence = "High" if len(raw_df) >= 2 else "Medium" if len(raw_df) > 0 else "Low"

    return {
        "bank": "boa",
        "parser": "BOA Parser",
        "confidence": confidence,
        "raw_rows": raw_df,
        "clean_df": clean_df,
    }