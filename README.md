# LedgerLens

**LedgerLens — Multi-Bank Statement Analytics Platform**

LedgerLens is a Python-based financial analytics platform that extracts and analyzes transactions from bank and credit card statement PDFs.

The system automatically detects the bank, parses the statement format, normalizes transactions into a unified dataset, and generates interactive spending insights.

## Live Demo

https://ledgerlens-analytics.streamlit.app
---

# Features

- Multi-bank statement parsing (AMEX, Chase, Bank of America)
- Automatic bank detection from PDF statements
- Transaction extraction and normalization
- Interactive analytics dashboard built with Streamlit
- Spending insights by category, merchant, and time
- CSV export of parsed and filtered transactions
- Debug mode with parser diagnostics and raw match preview
- Support for multiple statement uploads

---

# Project Architecture

```
PDF Statement
      ↓
Bank Detection
      ↓
Bank-Specific Parser
      ↓
Transaction Normalization
      ↓
Analytics Dashboard
```

---

# Tech Stack

- Python
- Streamlit
- Pandas
- Plotly
- pdfplumber
- python-dateutil

---

# Repository Structure

```
ledgerlens
│
├── app.py
├── requirements.txt
├── README.md
│
├── utils
│   ├── parser_router.py
│   ├── amex_parser.py
│   ├── chase_parser.py
│   ├── boa_parser.py
│   └── common.py
│
├── screenshots
│   └── dashboard.png
│
└── sample_statements
    └── demo_files.pdf
```

---

# Installation

### Clone the repository

```
git clone https://github.com/SharathReddyKottam/ledgerlens.git
```

### Move into the project folder

```
cd ledgerlens
```

### Create a virtual environment

```
python -m venv .venv
```

### Activate the environment

Mac / Linux

```
source .venv/bin/activate
```

Windows

```
.venv\Scripts\activate
```

### Install dependencies

```
pip install -r requirements.txt
```

---

# Run the Dashboard

Start the Streamlit app

```
streamlit run app.py
```

Open your browser at

```
http://localhost:8501
```

Upload bank statement PDFs to begin analysis.

---

# Example Insights

LedgerLens can automatically generate:

- Monthly spending trends
- Category-level expense distribution
- Merchant spending analysis
- Cross-bank spending comparison
- Transaction-level exports

---

# Future Improvements

- Support for additional bank formats
- Machine learning based transaction categorization
- Automatic Gmail statement ingestion
- Financial anomaly detection
- Recurring expense identification

---

# License

This project is open source and available under the MIT License.
