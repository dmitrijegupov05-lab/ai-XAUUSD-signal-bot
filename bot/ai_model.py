# bot/ai_model.py

import numpy as np
import requests
import json
from datetime import datetime

# ========== ПАРАМЕТРЫ МОДЕЛИ (из MQL5) ==========
LSTM_SIZE = 64
LOOKBACK = 100

# ========== ИНИЦИАЛИЗАЦИЯ ВЕСОВ ==========
def init_weights():
    np.random.seed(42)
    weights_lstm = np.random.randn(LOOKBACK, LSTM_SIZE) * 0.1
    weights_attention = np.random.randn(LSTM_SIZE, LSTM_SIZE) * 0.05
    return weights_lstm, weights_attention

WEIGHTS_LSTM, WEIGHTS_ATTENTION = init_weights()

# ========== ФУНКЦИИ АКТИВАЦИИ ==========
def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -100, 100)))

def tanh(x):
    return np.tanh(np.clip(x, -100, 100))

def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / (e_x.sum() + 1e-8)

# ========== ПОЛУЧЕНИЕ ДАННЫХ (Finnhub) ==========
def get_market_data(limit=120):
    try:
        url = f"https://api.finnhub.io/api/v1/forex/candle?symbol=OANDA:XAUUSD&resolution=5&count={limit}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if 'c' in data and len(data['c']) > LOOKBACK:
            return {
                'close': np.array(data['c']),
                'high': np.array(data['h']),
                'low': np.array(data['l']),
                'open': np.array(data['o']),
                'volume': np.array(data['v'])
            }
        return None
    except Exception as e:
        print(f"Ошибка данных: {e}")
        return None

# ========== РАСЧЁТ 10 ПРИЗНАКОВ ==========
def calculate_indicators(data):
    close = data['close']
    high = data['high']
    low = data['low']
    volume = data['volume']
    
    features = []
    for i in range(20, len(close)):
        # 1. Цена (нормализованная)
        price = close[i] / close[-1]
        
        # 2. RSI (14)
        gains = 0
        losses = 0
        for j in range(i-14, i):
            diff = close[j+1] - close[j]
            if diff >= 0:
                gains += diff
            else:
                losses += abs(diff)
        rsi = 100 - (100 / (1 + (gains / (losses + 0.0001)))) if losses > 0 else 100
        
        # 3. MACD (нормализованный)
        ema_fast = np.mean(close[i-12:i])
        ema_slow = np.mean(close[i-26:i])
        macd = (ema_fast - ema_slow) / (close[i] + 0.0001)
        
        # 4. ATR (нормализованный)
        atr = (high[i] - low[i]) / (close[i] + 0.0001)
        
        # 5. Стохастик
        lowest = np.min(low[i-5:i])
        highest = np.max(high[i-5:i])
        stoch = (close[i] - lowest) / (highest - lowest + 0.0001) * 100
        
        # 6. Моментум
        momentum = close[i] / close[i-10] - 1.0
        
        # 7. Полосы Боллинджера (%B)
        mean = np.mean(close[i-20:i])
        std = np.std(close[i-20:i])
        if std > 0:
            bb = (close[i] - (mean - 2*std)) / (4*std + 0.0001)
        else:
            bb = 0.5
        
        # 8. Объём (нормализованный)
        vol = volume[i] / (np.mean(volume[i-30:i]) + 0.0001)
        
        # 9. Уровень поддержки/сопротивления
        sr = (high[i] - np.min(low[i-20:i])) / (np.max(high[i-20:i]) - np.min(low[i-20:i]) + 0.0001)
        
        # 10. Корреляция (имитация)
        corr = np.sin(i * 0.01) * 0.5 + 0.5
        
        # Собираем и нормализуем в [-1, 1]
        vec = np.array([price, rsi/100, macd, atr, stoch/100, momentum, bb, vol/10, sr, corr])
        vec = (vec - 0.5) * 2.0
        features.append(vec)
    
    return np.array(features)

# ========== LSTM ЯЧЕЙКА ==========
def lstm_cell(input_vec, h_prev, c_prev):
    input_gate = sigmoid(np.dot(input_vec, np.random.randn(10, LSTM_SIZE) * 0.1))
    forget_gate = sigmoid(np.dot(input_vec, np.random.randn(10, LSTM_SIZE) * 0.1))
    output_gate = sigmoid(np.dot(input_vec, np.random.randn(10, LSTM_SIZE) * 0.1))
    cell_gate = tanh(np.dot(input_vec, np.random.randn(10, LSTM_SIZE) * 0.1))
    
    c_new = forget_gate * c_prev + input_gate * cell_gate
    h_new = output_gate * tanh(c_new)
    return h_new, c_new

# ========== ATTENTION ==========
def attention(hidden):
    scores = np.dot(hidden, WEIGHTS_ATTENTION)
    att_weights = softmax(scores)
    attended = hidden * att_weights
    return attended

# ========== AI ПРОГНОЗ ==========
def get_ai_prediction(features):
    if len(features) < LOOKBACK:
        return 0.0
    
    h_state = np.zeros(LSTM_SIZE)
    c_state = np.zeros(LSTM_SIZE)
    
    for i in range(min(LOOKBACK, len(features))):
        h_state, c_state = lstm_cell(features[i], h_state, c_state)
    
    attended = attention(h_state)
    output = np.sum(attended * np.linspace(-1, 1, LSTM_SIZE)) * 0.01
    return np.clip(output, -1.0, 1.0)

# ========== ГЕНЕРАЦИЯ СИГНАЛА ==========
def generate_signal():
    data = get_market_data(120)
    if not data:
        return {
            'signal': 'HOLD',
            'confidence': 'LOW',
            'price': 0,
            'prediction': 0,
            'reason': 'Нет данных от API',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    
    features = calculate_indicators(data)
    if len(features) == 0:
        return {
            'signal': 'HOLD',
            'confidence': 'LOW',
            'price': data['close'][-1],
            'prediction': 0,
            'reason': 'Недостаточно признаков',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    
    prediction = get_ai_prediction(features)
    current_price = data['close'][-1]
    
    if prediction > 0.3:
        signal = 'BUY'
        confidence = 'HIGH' if prediction > 0.6 else 'MEDIUM'
        reason = f"AI прогноз: {prediction:.3f} (бычий)"
    elif prediction < -0.3:
        signal = 'SELL'
        confidence = 'HIGH' if prediction < -0.6 else 'MEDIUM'
        reason = f"AI прогноз: {prediction:.3f} (медвежий)"
    else:
        signal = 'HOLD'
        confidence = 'LOW'
        reason = f"AI прогноз: {prediction:.3f} (нейтрально)"
    
    return {
        'signal': signal,
        'confidence': confidence,
        'price': round(current_price, 2),
        'prediction': round(prediction, 3),
        'reason': reason,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
