import re
import pandas as pd
import pdfplumber
from utils.common import to_fileobj, finalize_dataframe


def _normalize_robinhood_amount(value: str) -> str:
    value = value.strip()
    # Robinhood credits often end with trailing minus: 1298.18-
    if value.endswith("-"):
        value = "-" + value[:-1]
    return value


def extract_robinhood_transactions(pdf_file):
    fileobj = to_fileobj(pdf_file)
    rows = []

    # Robinhood transaction row examples:
    # 01/05 01/06 2469216QM31RRB2BJ TST*INDIA BAZAAR 571-407-5303 VA 34.07
    # 01/12 01/12 7442057QX00XSR3EG PAYMENT - THANK YOU 1,298.18-
    # 01/27 01/27 7494300DQAP43KGQR COSTCO WHSE #0204 FAIRFAX VA CREDIT 5.54-
    #
    # Capture:
    # tran date, post date, ref no, description, amount
    pattern = re.compile(
        r"^(?P<date>\d{2}/\d{2})"                              # tran date
        r"\s+\d{2}/\d{2}"                                      # post date
        r"\s+[A-Z0-9]{10,}"                                    # reference number
        r"\s+(?P<description>.+?)"                             # description
        r"\s+(?P<amount>\d{1,3}(?:,\d{3})*\.\d{2}-?|"
        r"-?\d{1,3}(?:,\d{3})*\.\d{2}|"
        r"\$?\d{1,3}(?:,\d{3})*\.\d{2}-?)$"
    )

    with pdfplumber.open(fileobj) as pdf:
        in_transactions = False

        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            for raw_line in text.splitlines():
                line = re.sub(r"\s+", " ", raw_line).strip()
                upper_line = line.upper()

                if upper_line == "TRANSACTIONS":
                    in_transactions = True
                    continue

                if not in_transactions:
                    continue

                # stop once totals/interest section starts
                if upper_line.startswith("TOTAL FEES FOR THIS PERIOD") or upper_line.startswith("INTEREST CHARGED"):
                    break

                # ignore continuation detail lines like:
                # - 01/16 IN RUPEE
                # - 01/16 999.00 X 0.01109109
                if line.startswith("- "):
                    continue

                match = pattern.match(line)
                if match:
                    rows.append(
                        {
                            "page": page_num,
                            "date": f"{match.group('date')}/26",
                            "description": match.group("description"),
                            "amount": _normalize_robinhood_amount(match.group("amount")),
                            "matched_line": line,
                        }
                    )

    raw_df = pd.DataFrame(rows)

    clean_df = finalize_dataframe(
        raw_df[["date", "description", "amount"]].copy() if not raw_df.empty else pd.DataFrame(),
        bank_name="ROBINHOOD",
        date_format="%m/%d/%y",
        invert_sign=False,
        account_type="credit",
    )

    confidence = "High" if len(raw_df) >= 5 else "Medium" if len(raw_df) > 0 else "Low"

    return {
        "bank": "robinhood",
        "parser": "Robinhood Parser",
        "confidence": confidence,
        "raw_rows": raw_df,
        "clean_df": clean_df,
    }