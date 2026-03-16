from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import os
import json
from sklearn.ensemble import HistGradientBoostingRegressor
from datetime import datetime
import traceback

app = Flask(__name__)
RAW_FOLDER = os.path.join(os.path.dirname(__file__), 'raw')

# ─── Helpers ────────────────────────────────────────────────────────────────

def get_material_files():
    if not os.path.exists(RAW_FOLDER):
        return []
    return sorted([f for f in os.listdir(RAW_FOLDER) if f.endswith('.xlsx')])

def read_material(file_name):
    path = os.path.join(RAW_FOLDER, file_name)
    df = pd.read_excel(path)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    return df

def get_stock_overview():
    files = get_material_files()
    result = []
    for fname in files:
        try:
            df = read_material(fname)
            max_closing = float(df['Closing'].max())
            latest_closing = float(df['Closing'].iloc[-1])
            avg_closing = float(df['Closing'].mean())
            terminal_level = avg_closing * 0.6
            if latest_closing >= max_closing * 0.5:
                status = 'green'
            elif latest_closing >= max_closing * 0.25:
                status = 'yellow'
            else:
                status = 'red'
            result.append({
                'file': fname,
                'name': fname.replace('.xlsx', '').replace('_', ' '),
                'max_closing': round(max_closing, 2),
                'latest_closing': round(latest_closing, 2),
                'terminal_level': round(terminal_level, 2),
                'status': status,
                'pct': round((latest_closing / max_closing) * 100, 1) if max_closing > 0 else 0
            })
        except Exception as e:
            print(f"Error reading {fname}: {e}")
    return result

def get_alerts():
    files = get_material_files()
    alerts = []
    for fname in files:
        try:
            df = read_material(fname)
            material_name = fname.replace('.xlsx', '').replace('_', ' ')
            # Check unused 30 days
            latest_date = df['Date'].max()
            threshold = latest_date - pd.Timedelta(days=30)
            recent = df[df['Date'] >= threshold]
            if recent['Closing'].nunique() == 1:
                alerts.append({'type': 'warning', 'msg': f"{material_name}: Not used in the past 30 days"})
            # Check terminal level
            avg = df['Closing'].mean()
            terminal = avg * 0.6
            latest = float(df['Closing'].iloc[-1])
            if latest < terminal:
                alerts.append({'type': 'danger', 'msg': f"{material_name}: Stock below terminal level — restock immediately!"})
        except Exception as e:
            print(f"Alert error {fname}: {e}")
    return alerts

def predict_for_material(file_name):
    df = read_material(file_name)
    last_non_zero = df[df['Total'] > 0]
    if not last_non_zero.empty:
        df = last_non_zero.copy()
    last_10_months = df[df['Date'] >= df['Date'].max() - pd.DateOffset(months=10)].copy()
    for i in range(1, 22):
        last_10_months[f'Total_lag_{i}'] = last_10_months['Total'].shift(i)
    drop_cols = ['Date', 'Total', 'Material'] if 'Material' in last_10_months.columns else ['Date', 'Total']
    X = last_10_months.drop(drop_cols, axis=1)
    y = last_10_months['Total']
    model = HistGradientBoostingRegressor(max_iter=100, learning_rate=0.1, random_state=42)
    model.fit(X, y)
    last_day = X.tail(1)
    predicted = model.predict(last_day)[0]
    latest_closing = float(last_10_months.iloc[-1]['Closing'])
    if predicted > 0:
        days_remaining = latest_closing / predicted
        days_high = latest_closing / (predicted * 1.3)
        days_low = latest_closing / (predicted * 0.7)
    else:
        days_remaining = days_high = days_low = 0
    def to_readable(days):
        days = int(days)
        if days >= 30:
            m = days // 30
            d = days % 30
            return f"{m} month{'s' if m>1 else ''}" + (f" {d//7} week{'s' if d//7>1 else ''}" if d >= 7 else "")
        elif days >= 7:
            w = days // 7
            return f"{w} week{'s' if w>1 else ''}"
        else:
            return f"{days} day{'s' if days!=1 else ''}"

    # Charts data
    df2 = read_material(file_name)
    last_305 = df2.set_index('Date').tail(305)['Closing']
    last_30 = df2.set_index('Date').tail(30)['Closing']
    bar_dates = [str(d.date()) for d in last_305.index]
    bar_vals = [round(float(v), 2) for v in last_305.values]
    line_dates = [str(d.date()) for d in last_30.index]
    line_vals = [round(float(v), 2) for v in last_30.values]

    return {
        'opening': round(latest_closing, 2),
        'predicted_usage': round(predicted, 2),
        'days_remaining': to_readable(days_remaining),
        'days_high': to_readable(days_high),
        'days_low': to_readable(days_low),
        'days_remaining_num': int(days_remaining),
        'bar_dates': bar_dates,
        'bar_vals': bar_vals,
        'line_dates': line_dates,
        'line_vals': line_vals,
    }

# ─── Routes ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    materials = get_material_files()
    stock = get_stock_overview()
    alerts = get_alerts()
    return render_template('index.html', materials=materials, stock=stock, alerts=alerts)

@app.route('/api/predict/<file_name>')
def api_predict(file_name):
    try:
        data = predict_for_material(file_name)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()})

@app.route('/api/add_data', methods=['POST'])
def api_add_data():
    try:
        payload = request.get_json()
        file_name = payload['file_name']
        date_str = payload['date']
        purchase = float(payload['purchase'])
        usage = float(payload['usage'])
        path = os.path.join(RAW_FOLDER, file_name)
        df = pd.read_excel(path)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        last_closing = float(df['Closing'].dropna().iloc[-1])
        new_closing = last_closing + purchase - usage
        new_row = {
            'Material': None,
            'Date': pd.to_datetime(date_str),
            'Opening': last_closing,
            'Purchase': purchase,
            'Issues': 0,
            'Line_1': 0,
            'Line_2': 0,
            'Total': usage,
            'moisture': 0,
            'percentage': 0,
            'Closing': round(new_closing, 3)
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_excel(path, index=False)
        return jsonify({'success': True, 'new_closing': round(new_closing, 2)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upload', methods=['POST'])
def api_upload():
    try:
        file = request.files['file']
        df = pd.read_excel(file)
        df = df.iloc[3:].reset_index(drop=True)
        df.drop(df.columns[4:7], axis=1, inplace=True)
        df.columns = range(df.shape[1])
        new_columns = {0:'Material',1:'Date',2:'Opening',3:'Purchase',4:'Issues',
                       5:'Line_1',6:'Line_2',7:'Total',8:'moisture',9:'percentage',10:'Closing'}
        df.rename(columns=new_columns, inplace=True)
        material_indices = []
        start_index = None
        for index, row in df.iterrows():
            if not pd.isnull(row[0]):
                if start_index is None:
                    start_index = index
                elif start_index is not None:
                    material_indices.append((start_index, index - 1))
                    start_index = index
        if start_index is not None:
            material_indices.append((start_index, df.index[-2]))
        saved = []
        for start, end in material_indices:
            material_name = df.iloc[start, 0]
            excel_file = os.path.join(RAW_FOLDER, f"{material_name}.xlsx")
            with pd.ExcelWriter(excel_file) as writer:
                df.iloc[start:end+1].to_excel(writer, index=False, header=True)
            saved.append(str(material_name))
        return jsonify({'success': True, 'saved': saved})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=False)
