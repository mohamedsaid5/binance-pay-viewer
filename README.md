# Binance Pay — Payment History Viewer

> **Note:** This project was built with the assistance of AI (Claude by Anthropic).

A desktop application that mirrors the [Binance Payment History](https://www.binance.com/en/my/orders/payment) page.
It fetches your Binance Pay transactions through the official REST API, displays them in a familiar dark-themed table, and lets you export, chart, and filter the data.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

| Feature | Description |
|---|---|
| **Auto-load** | Fetches the last 30 days of transactions on startup — no manual search needed |
| **Binance-style UI** | Dark theme matching the real Binance Payment History page |
| **Type filter** | Filter by All / Received / Paid |
| **Period presets** | Today, Yesterday, Last 7/14/30/90 Days, or Custom date range |
| **Quick search** | Live search across all fields (name, amount, order ID, note…) |
| **Order ID lookup** | Paste comma-separated 18-digit order IDs to find specific transactions |
| **Export to PDF** | Professionally formatted landscape PDF with page numbers |
| **Export to Excel** | `.xlsx` export via pandas + openpyxl |
| **Column selection** | Choose which columns to include in your export |
| **Transaction details** | Click "Details" on any row to see the full record |
| **Advanced filters** | Filter by amount range, currency, date, user name, or note text |
| **Dashboard** | Summary cards + charts (time series, direction pie, top users bar chart) |
| **Chart view** | Standalone line chart of transaction amounts over time |
| **Auto-refresh** | Optional real-time polling every 30 seconds |
| **Large date ranges** | Automatically splits requests into 90-day chunks (API limit) |

---

## Binance API — Endpoint Reference

This app uses **two** public Binance endpoints:

### 1. Payment Transaction History

| | |
|---|---|
| **Endpoint** | `GET /sapi/v1/pay/transactions` |
| **Docs** | [binance-docs.github.io/apidocs/spot/en/#get-pay-trade-history](https://binance-docs.github.io/apidocs/spot/en/#get-pay-trade-history) |
| **Auth** | HMAC SHA-256 signed request (requires API key + secret) |
| **Rate limit** | Uses the UID rate limit |
| **Max range** | 90 days per request (`startTime` → `endTime`) |
| **Page size** | Up to 100 records per page |

**Parameters used:**

| Parameter | Type | Description |
|---|---|---|
| `startTime` | LONG | Start of the query range (Unix ms) |
| `endTime` | LONG | End of the query range (Unix ms) |
| `limit` | INT | Records per page (max 100) |
| `page` | INT | Page number (1-based) |
| `timestamp` | LONG | Current time (Unix ms) |
| `recvWindow` | LONG | Request validity window (ms) |
| `signature` | STRING | HMAC SHA-256 signature |

**Response fields used:**

| Field | Description |
|---|---|
| `orderId` | Unique 18-digit transaction identifier |
| `transactionTime` | Unix timestamp in milliseconds |
| `amount` | Transaction amount (positive = received, negative = sent) |
| `currency` | e.g. USDT, BNB, BTC |
| `payerInfo.name` | Sender / receiver display name |
| `direction` | `RECEIVE` or `SEND` |
| `note` | Optional note attached to the payment |

### 2. Ticker Price (for live conversion rates)

| | |
|---|---|
| **Endpoint** | `GET /api/v3/ticker/price` |
| **Docs** | [binance-docs.github.io/apidocs/spot/en/#symbol-price-ticker](https://binance-docs.github.io/apidocs/spot/en/#symbol-price-ticker) |
| **Auth** | None (public endpoint) |

Used to fetch live BNB/USDT and BTC/USDT prices for the dashboard currency conversion.

---

## How to Generate Your Binance API Key

1. Log in to [Binance](https://www.binance.com/)
2. Go to **Account** → **API Management**
   - Direct link: [https://www.binance.com/en/my/settings/api-management](https://www.binance.com/en/my/settings/api-management)
3. Click **Create API** → choose **System generated**
4. Give it a label (e.g. `PaymentViewer`)
5. Complete 2FA verification
6. **Copy** both the **API Key** and **Secret Key** (the secret is shown only once!)

### Required Permissions

- ✅ **Enable Reading** — needed to read payment history
- ❌ Enable Trading — **not needed** (leave unchecked)
- ❌ Enable Withdrawals — **not needed** (leave unchecked)

> ⚠️ Only grant **read** permissions. This app never places orders or moves funds.

### IP Restriction (recommended)

For extra security, restrict the API key to your own IP address in the API settings page.

---

## Setup & Installation

### Prerequisites

- Python 3.10 or newer
- A Binance account with an API key (read-only)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/mohamedsaid5/binance-pay-viewer.git
cd binance-pay-viewer

# 2. (Optional) Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux

# 5. Edit .env and paste your API key and secret
#    API_KEY=...
#    API_SECRET=...

# 6. Run the app
python main.py
```

---

## Project Structure

```
binance-pay-viewer/
├── main.py            # Entry point — starts the app
├── main_window.py     # Main window UI (Binance-style table, filters, toolbar)
├── api.py             # Binance API calls + background worker thread
├── config.py          # Environment loading, constants, logging setup
├── utils.py           # Time conversion, parsing, currency helpers
├── theme.py           # Binance dark theme, colours, SVG icons, stylesheet
├── dialogs.py         # Column selection, advanced filters, detail dialog
├── dashboard.py       # Dashboard window with charts (time, direction, users)
├── export.py          # PDF export (reportlab)
├── icons/
│   ├── binance_pay_icon.png
│   └── binance_pay_icon.ico
├── requirements.txt   # Python dependencies
├── .env.example       # Template for API credentials
├── .gitignore
├── LICENSE
└── README.md
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `PyQt6` | GUI framework |
| `PyQt6-Charts` | Dashboard charts |
| `requests` | HTTP calls to Binance API |
| `pandas` | Data manipulation for Excel export |
| `openpyxl` | Excel `.xlsx` writer |
| `reportlab` | PDF generation |
| `python-dotenv` | Load `.env` environment variables |

All listed in `requirements.txt`.

---

## License

MIT — see [LICENSE](LICENSE).
