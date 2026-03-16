# ⚙️ Raw Material Predictive Model

<div align="center">

# 🌐 [👉 CLICK HERE — LIVE WEB APP](https://huggingface.co/spaces/Job6742/Raw_Material_Predictor)
### 🔗 https://huggingface.co/spaces/Job6742/Raw_Material_Predictor

*ML-powered inventory intelligence dashboard — works in any browser, no installation needed*

</div>

---

## 📌 What Is This?

A full-stack AI application that monitors raw material stock levels in real time, predicts how long current stock will last using machine learning, and raises automatic alerts when materials are running low or unused.

Originally built as a **PyQt5 desktop application**, it was rebuilt as a **Flask web app** and deployed on **Hugging Face Spaces** so anyone can access it via a browser link.

---

## ✅ Features

| Feature | Description |
|---|---|
| 📊 Stock level bars | Color-coded visual bars (green / yellow / red) per material |
| 🤖 ML Prediction | Predicts daily consumption using HistGradientBoostingRegressor |
| 📅 Days Remaining | Estimates how long stock will last (normal / high / low range) |
| ⚠️ Alerts Panel | Flags materials unused for 30+ days or below terminal level |
| 📁 Upload Excel | Upload master Excel file — auto-splits by material |
| ➕ Add Data | Log daily purchase and usage via web form |
| 📈 Charts | 10-month bar chart + 30-day trend line chart per material |

---

## 🏗️ Full App Pipeline

```
Custom Excel Dataset (raw/ folder)
         ↓
Flask Backend (app.py)
   ├── Read & parse Excel files (pandas)
   ├── Calculate stock overview (max, latest, terminal level)
   ├── Run ML prediction (scikit-learn)
   │     ├── Filter last 10 months of non-zero data
   │     ├── Engineer 21 lag features
   │     ├── Train HistGradientBoostingRegressor
   │     └── Predict daily consumption → days remaining
   ├── Generate alerts (unused 30d + below terminal)
   └── Serve HTML dashboard
         ↓
Browser Dashboard (index.html)
   ├── Stock level bars (click to analyse)
   ├── Prediction metrics (opening, usage, days)
   ├── Confidence range (high / normal / low consumption)
   ├── Chart.js charts (10-month bar + 30-day line)
   ├── Add data form
   └── Upload Excel file
```

---

## 🧠 Machine Learning Pipeline — Step by Step

### Step 1 — Data Loading

Each material has its own `.xlsx` file inside the `raw/` folder. The file contains daily records with these columns:

| Column | Description |
|---|---|
| `Date` | Date of the record |
| `Opening` | Opening stock for the day |
| `Purchase` | Quantity purchased that day |
| `Line_1` | Consumption from production Line 1 |
| `Line_2` | Consumption from production Line 2 |
| `Total` | Total consumption (Line_1 + Line_2) |
| `moisture` | Moisture adjustment value |
| `percentage` | Moisture percentage |
| `Closing` | Closing stock = Opening + Purchase − Total |

```python
df = pd.read_excel(file_path)
df['Date'] = pd.to_datetime(df['Date'])
```

---

### Step 2 — Data Filtering

Only rows with **non-zero consumption** are used. This removes days where the factory was idle, which would bias the model toward predicting zero usage.

```python
last_non_zero = df[df['Total'] > 0]
if not last_non_zero.empty:
    df = last_non_zero.copy()
```

Then the data is further narrowed to the **last 10 months** to keep predictions relevant to recent consumption patterns:

```python
last_10_months = df[df['Date'] >= df['Date'].max() - pd.DateOffset(months=10)].copy()
```

---

### Step 3 — Feature Engineering (Lag Features)

This is the most important ML step. Since consumption is a **time series** (today's usage depends on recent days), we create **21 lag features** — each one is the `Total` consumption from N days ago.

```python
for i in range(1, 22):
    last_10_months[f'Total_lag_{i}'] = last_10_months['Total'].shift(i)
```

This gives the model a "memory" of the past 21 days of consumption, allowing it to detect weekly cycles, trends, and patterns.

**Why 21 lags?** It covers exactly 3 weeks — enough to capture weekly production cycles without overfitting on older patterns.

---

### Step 4 — Model: HistGradientBoostingRegressor

The model used is **`HistGradientBoostingRegressor`** from scikit-learn.

```python
from sklearn.ensemble import HistGradientBoostingRegressor

model = HistGradientBoostingRegressor(
    max_iter=100,
    learning_rate=0.1,
    random_state=42
)
model.fit(X, y)
```

**Why this model?**

| Property | Detail |
|---|---|
| Algorithm | Gradient Boosted Decision Trees (histogram-based) |
| Handles missing values | ✅ Yes — built-in NaN support (important since lag features create NaN rows) |
| Fast training | ✅ Yes — histogram binning makes it much faster than standard GBT |
| Robust to outliers | ✅ Yes — tree-based, not sensitive to extreme values |
| Works on small datasets | ✅ Yes — 300–700 rows is sufficient |

Gradient Boosting works by training many shallow decision trees **sequentially** — each tree corrects the errors of the previous one. The histogram variant groups continuous values into bins, making it significantly faster on tabular data.

---

### Step 5 — Prediction

The model predicts **tomorrow's consumption** based on the last 21 days of actual usage:

```python
last_day_features = X.tail(1)
predicted_total = model.predict(last_day_features)[0]
```

---

### Step 6 — Days Remaining Calculation

Using the predicted daily consumption and the current closing stock:

```python
days_remaining = current_closing / predicted_total
```

A **±30% confidence range** is also calculated:

```python
days_high = current_closing / (predicted_total * 1.3)   # High consumption scenario
days_low  = current_closing / (predicted_total * 0.7)   # Low consumption scenario
```

This gives three estimates: worst case, expected, and best case.

---

### Step 7 — Alert System

Two alert types run automatically on page load:

**Alert 1 — Unused Material (30 days)**
```python
recent = df[df['Date'] >= latest_date - pd.Timedelta(days=30)]
if recent['Closing'].nunique() == 1:
    # Stock hasn't changed in 30 days — material not being used
    alerts.append(...)
```

**Alert 2 — Below Terminal Level**
```python
terminal_level = average_closing * 0.6   # 60% of historical average
if latest_closing < terminal_level:
    # Critical — restock immediately
    alerts.append(...)
```

---

### Step 8 — Stock Health Color Coding

Each material card is colored based on its current stock relative to its historical maximum:

```python
if latest_closing >= max_closing * 0.50:   # Above 50% of max → GREEN
elif latest_closing >= max_closing * 0.25: # Above 25% of max → YELLOW
else:                                       # Below 25% of max → RED
```

---

## 🔄 Application Pipeline Diagram

```
                    ┌─────────────────────────────┐
                    │     App Starts (Flask)       │
                    └────────────┬────────────────┘
                                 │
                    ┌────────────▼────────────────┐
                    │       setupUi() / index()    │
                    │  Builds dashboard on load    │
                    └──┬─────────┬──────────┬─────┘
                       │         │          │
           ┌───────────▼─┐  ┌────▼────┐  ┌─▼──────────────┐
           │ Load raw/   │  │Populate │  │ Check materials │
           │ folder      │  │dropdown │  │ (alerts)        │
           │ Max+Latest  │  │         │  │ 30d + terminal  │
           └───────────┬─┘  └────┬────┘  └─┬──────────────┘
                       │         │          │
           ┌───────────▼─┐  ┌────▼────┐  ┌─▼──────────────┐
           │Material     │  │ Combo   │  │ Alert labels    │
           │Widget bars  │  │ box     │  │ shown on UI     │
           └─────────────┘  └─────────┘  └────────────────┘
                                 │
                    ┌────────────▼────────────────┐
                    │     User Interaction         │
                    │  Select / Upload / Add Data  │
                    └──┬──────────┬───────────────┘
                       │          │              │
          ┌────────────▼─┐  ┌─────▼──────┐  ┌──▼──────────┐
          │Select material│  │Upload Excel│  │Add data form│
          │→ prediction   │  │Parse+split │  │Calc Closing │
          └──────┬────────┘  └─────┬──────┘  └──┬──────────┘
                 │                 │             │
          ┌──────▼───────┐  ┌──────▼─────┐  ┌──▼──────────┐
          │ ML Pipeline  │  │Save per-   │  │Append row   │
          │ 21 lag feats │  │material    │  │to .xlsx     │
          │ HGBRegressor │  │.xlsx files │  │             │
          └──────┬───────┘  └────────────┘  └─────────────┘
                 │
          ┌──────▼───────┐
          │ LCD metrics  │
          │ + Charts     │
          │ + Days left  │
          └──────────────┘
```

---

## 🗂️ Project Structure

```
raw-material-predictor/
├── app.py                       # Flask backend — all ML + API routes
├── Dockerfile                   # Docker config for HF Spaces
├── requirements.txt             # Python dependencies
├── templates/
│   └── index.html               # Full dashboard UI (HTML + Chart.js)
└── raw/                         # Material Excel files (sample data)
    ├── GYPSUM_PHOSPO.xlsx
    ├── FIRE_CLAY_AT_FACTORY.xlsx
    ├── FLYASH_-_WET_-2.xlsx
    ├── FLYASH_DRY.xlsx
    ├── FLYASH_WET.xlsx
    └── GYPSUM_IMPORTED.xlsx
```

> ⚠️ The Excel files in `raw/` contain **sample/demo data only**. Replace with your actual material files in the same column format.

---

## 💻 Run Locally from Source Code

### Prerequisites
- Python 3.9+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/Job6742/raw-material-predictor.git
cd raw-material-predictor
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
python app.py
```

### 4. Open in browser

```
http://localhost:7860
```

---

## 📦 Download & Run the Desktop .exe (Windows)

> The original version of this app was built as a standalone Windows desktop application using PyQt5.

### Steps:

1. Go to 👉 **[Releases](https://github.com/Job6742/raw-material-predictor/releases/latest)**
2. Download **`RawMaterialPredictor.exe`**
3. Place the `.exe` in a folder that also contains a `raw/` subfolder with your `.xlsx` material files
4. Double-click the `.exe` — no Python installation required

### Folder structure for the .exe:

```
📁 Your Folder/
├── RawMaterialPredictor.exe
└── 📁 raw/
    ├── MATERIAL_1.xlsx
    ├── MATERIAL_2.xlsx
    └── ...
```

### To rebuild the .exe yourself:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=ramco_logo.ico main.py
# Output will be in dist/RawMaterialPredictor.exe
```

---

## 🚀 Flask Deployment on Hugging Face Spaces

### Step 1 — Create a Hugging Face account
Go to [huggingface.co](https://huggingface.co) and sign up.

### Step 2 — Create a new Space
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Set **SDK → Docker**, Visibility → **Public**
4. Click **"Create Space"**

### Step 3 — Upload your files
Go to **Files** tab → **"Add file"** → **"Upload files"**

Upload in this structure:
```
app.py            → root
Dockerfile        → root
requirements.txt  → root
templates/index.html
raw/GYPSUM_PHOSPO.xlsx
raw/FIRE_CLAY_AT_FACTORY.xlsx
... (all 6 Excel files)
```

### Step 4 — Wait for build
- Go to **App** tab
- 🟡 **Building** — wait 3–5 minutes
- 🟢 **Running** — your app is live!

### Step 5 — Share your link
```
https://huggingface.co/spaces/Job6742/raw-material-predictor
```

### How the Dockerfile works

```dockerfile
FROM python:3.10-slim       # Base Python image
WORKDIR /app                # Set working directory
COPY requirements.txt .     # Copy dependency list
RUN pip install ...         # Install all packages
COPY . .                    # Copy all project files
EXPOSE 7860                 # HF Spaces uses port 7860
CMD ["python", "app.py"]    # Start the Flask server
```

HF Spaces builds this Docker container automatically every time you push a file change.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask (Python) |
| ML Model | scikit-learn — HistGradientBoostingRegressor |
| Data Processing | pandas, numpy |
| Charts | Chart.js (browser-side) |
| Frontend | HTML5, CSS3, Vanilla JS |
| Deployment | Hugging Face Spaces (Docker) |
| Excel I/O | openpyxl (via pandas) |
| Desktop Version | PyQt5, matplotlib, watchdog |

---

## 📋 Requirements

```
flask
pandas
scikit-learn
numpy
openpyxl
```

---

## 📄 License

This project is licensed under the **MIT License** — free to use, modify, and distribute.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 👤 Author

**Job6742**
- 🤗 Hugging Face: [@Job6742](https://huggingface.co/Job6742)
- 🐙 GitHub: [@Job6742](https://github.com/ponjose004/Raw-Material-Prediction)

---

> 💡 *This project demonstrates end-to-end ML deployment — from a custom industrial dataset, through feature engineering and gradient boosting, to a live browser-accessible web application.*
