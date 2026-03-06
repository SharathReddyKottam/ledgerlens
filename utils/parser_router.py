from io import BytesIO
import pdfplumber

from utils.amex_parser import extract_amex_transactions
from utils.chase_parser import extract_chase_transactions
from utils.boa_parser import extract_boa_transactions


def detect_bank(pdf_file) -> str:
    if hasattr(pdf_file, "read"):
        file_bytes = pdf_file.read()
        try:
            pdf_file.seek(0)
        except Exception:
            pass
    else:
        file_bytes = pdf_file

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        first_page_text = pdf.pages[0].extract_text() or ""

    text = first_page_text.upper()

    if "JPMORGAN CHASE BANK" in text or "CHASE COLLEGE CHECKING" in text or "CHASE.COM" in text:
        return "chase"

    if "BANK OF AMERICA" in text:
        return "boa"

    if "AMERICAN EXPRESS®" in text or "AMERICAN EXPRESS GOLD CARD" in text or "ACCOUNT ENDING" in text:
        return "amex"

    return "unknown"


def extract_transactions(pdf_file):
    bank = detect_bank(pdf_file)

    if bank == "amex":
        return extract_amex_transactions(pdf_file)
    elif bank == "chase":
        return extract_chase_transactions(pdf_file)
    elif bank == "boa":
        return extract_boa_transactions(pdf_file)
    else:
        return {
            "bank": "unknown",
            "parser": "Unknown",
            "confidence": "Low",
            "raw_rows": None,
            "clean_df": None,
        }