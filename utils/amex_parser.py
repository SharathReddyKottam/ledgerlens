import re
import pandas as pd
import pdfplumber
from utils.common import to_fileobj, finalize_dataframe


def extract_amex_transactions(pdf_file):
    fileobj = to_fileobj(pdf_file)
    rows = []

    pattern = re.compile(
        r"^(?P<date>\d{2}/\d{2}/\d{2})\*?\s+(?P<description>.+?)\s+(?P<amount>-?\$?\d+(?:,\d{3})*\.\d{2})$"
    )

    with pdfplumber.open(fileobj) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for raw_line in text.splitlines():
                line = re.sub(r"\s+", " ", raw_line).strip()
                match = pattern.match(line)
                if match:
                    rows.append(
                        {
                            "page": page_num,
                            "date": match.group("date"),
                            "description": match.group("description"),
                            "amount": match.group("amount"),
                            "matched_line": line,
                        }
                    )

    raw_df = pd.DataFrame(rows)

    clean_df = finalize_dataframe(
        raw_df[["date", "description", "amount"]].copy() if not raw_df.empty else pd.DataFrame(),
        bank_name="AMEX",
        date_format="%m/%d/%y",
        invert_sign=False,
        account_type="credit",
    )

    confidence = "High" if len(raw_df) >= 5 else "Medium" if len(raw_df) > 0 else "Low"

    return {
        "bank": "amex",
        "parser": "AMEX Parser",
        "confidence": confidence,
        "raw_rows": raw_df,
        "clean_df": clean_df,
    }