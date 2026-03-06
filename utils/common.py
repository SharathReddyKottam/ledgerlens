from io import BytesIO
import re
import pandas as pd


CATEGORY_MAP = {
    "STARBUCKS": "Coffee",
    "FOUNDATION COFFEE": "Coffee",
    "SPOTIFY": "Subscription",
    "OPENAI": "Subscription",
    "CHATGPT": "Subscription",
    "APPLE": "Subscription",
    "APPLE CARD PAYMENT": "Payment",
    "PRIME": "Subscription",
    "AMZN": "Subscription",
    "NETFLIX": "Subscription",
    "HULU": "Subscription",
    "DESI CHOWRASTHA": "Restaurant",
    "BLAZE PIZZA": "Restaurant",
    "PIZZA": "Restaurant",
    "LAYERED": "Restaurant",
    "CHATEAU": "Restaurant",
    "HAAGEN": "Dessert",
    "DOMINION ENERGY": "Utilities",
    "VIRGINIA NATURAL GAS": "Utilities",
    "ROBINHOOD": "Investment",
    "DIVIDEND": "Investment Income",
    "INTEREST": "Interest",
    "ACH DEPOSIT": "Transfer In",
    "ACH WITHDRAWAL": "Transfer Out",
    "CASH SWEEP": "Cash Movement",
    "AMERICAN EXPRESS": "Credit Card Payment",
    "AMERICANEXPRESS": "Credit Card Payment",
    "ZELLE PAYMENT FROM": "Transfer In",
    "ZELLE PAYMENT TO": "Transfer Out",
    "DEPOSIT": "Income",
    "MONTHLY SERVICE FEE": "Bank Fee",
    "MOBILE PAYMENT": "Payment",
    "PAYMENT THANK YOU": "Payment",

    # New Apple Card / Robinhood / merchant additions
    "SHOTTED SPECIALTY": "Coffee",
    "CAVA": "Restaurant",
    "NANDOS": "Restaurant",
    "HYDERABAD HOUSE": "Restaurant",
    "INDIA BAZAAR": "Groceries",
    "COSTCO": "Groceries",
    "DOORDASH": "Food Delivery",
    "PLAYSTATION": "Entertainment",
    "HBO": "Subscription",
    "ADOBE": "Subscription",
    "AMAZON": "Shopping",
    "AMAZON MKTPL": "Shopping",
    "HERTZ": "Travel",
    "FLAGSHIP CAR WASH": "Auto",
    "E Z PASS": "Transport",
    "MISCELLANEOUS CREDIT ADJ": "Credit Adjustment",
}


def to_fileobj(uploaded):
    if hasattr(uploaded, "read"):
        data = uploaded.read()
        try:
            uploaded.seek(0)
        except Exception:
            pass
        return BytesIO(data)
    return BytesIO(uploaded)


def clean_description(desc: str) -> str:
    desc = str(desc).upper()

    remove_words = [
        "APLPAY",
        "PAY OVER TIME",
        "SAN FRANCISCO",
        "INTERNET CHARGE",
        "FAIRFAX",
        "HERNDON",
        "CHANTILLY",
        "NEW YORK",
        "CA",
        "VA",
        "NY",
    ]

    for word in remove_words:
        desc = desc.replace(word, " ")

    desc = desc.replace("*", " ")
    desc = desc.replace("/", " ")
    desc = desc.replace("-", " ")

    desc = re.sub(r"\b\d+\b", " ", desc)

    replacements = {
        "APPLE COM BILL": "APPLE",
        "APPLE.COM BILL": "APPLE",
        "OPENAI CHATGPT SUBSCR": "OPENAI CHATGPT",
        "PRIME VIDEO CHANNELS AMZN.COM BILL": "PRIME VIDEO",
        "GMUBLAZEPIZZA": "BLAZE PIZZA",
        "TST DESI CHOWRASTHA HE": "DESI CHOWRASTHA",
        "TST DESI CHOWRASTHA": "DESI CHOWRASTHA",
        "TST LAYERED": "LAYERED",
        "TST CHATEAU DE": "CHATEAU DE",
        "MOBILE PAYMENT THANK YOU": "MOBILE PAYMENT",
        "ONLINE PAYMENT TO DOMINION ENERGY VIRGINIA": "DOMINION ENERGY",
        "AMERICANEXPRESS TRANSFER": "AMERICAN EXPRESS TRANSFER",
        "AMERICAN EXPRESS ACH PMT": "AMERICAN EXPRESS PAYMENT",
        "DD DOORDASHDASHPASS DOORDASH.COM": "DOORDASH",
        "ONLINE MOBILE PAYMENT": "ONLINE PAYMENT",
    }

    for old, new in replacements.items():
        desc = desc.replace(old, new)

    return " ".join(desc.split())


def categorize(desc: str) -> str:
    desc = str(desc).upper()
    for key, value in CATEGORY_MAP.items():
        if key in desc:
            return value
    return "Other"


def finalize_dataframe(
        df: pd.DataFrame,
        bank_name: str,
        date_format: str = "%m/%d/%y",
        invert_sign: bool = False,
        account_type: str = "credit",
) -> pd.DataFrame:
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"], format=date_format, errors="coerce")
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    if invert_sign:
        df["amount"] = -df["amount"]

    df = df.dropna(subset=["date", "amount"]).reset_index(drop=True)

    df["description_raw"] = df["description"]
    df["description"] = df["description"].apply(clean_description)
    df["category"] = df["description"].apply(categorize)
    df["bank"] = bank_name
    df["account_type"] = account_type

    return df