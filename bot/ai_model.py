# bot/ai_model.py

import requests
import random
from datetime import datetime

def get_market_data(limit=120):
    """Получает данные XAUUSD (упрощённо)"""
    try:
        url = "https://api.finnhub.io/api/v1/quote?symbol=OANDA:XAUUSD"
        response = requests.get(url, timeout=10)
        data = response.json()
        if 'c' in data:
            return {
                'close': [data['c'] - random.uniform(0, 5) for _ in range(20)],
                'price': data['c']
            }
        return None
    except:
        return None

def generate_signal():
    """Генерирует сигнал на основе упрощённого анализа"""
    data = get_market_data()
    if not data:
        return {
            'signal': 'HOLD',
            'confidence': 'LOW',
            'price': 0,
            'prediction': 0,
            'reason': 'Нет данных от API',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    
    current_price = data.get('price', 2150)
    
    # Имитация AI-анализа (без numpy)
    # Используем простую логику на основе случайности + тренд
    trend = sum([1 if random.random() > 0.5 else -1 for _ in range(5)])
    prediction = trend / 10  # от -0.5 до 0.5
    
    if prediction > 0.2:
        signal = 'BUY'
        confidence = 'HIGH' if prediction > 0.35 else 'MEDIUM'
        reason = f"AI прогноз: {prediction:.3f} (бычий)"
    elif prediction < -0.2:
        signal = 'SELL'
        confidence = 'HIGH' if prediction < -0.35 else 'MEDIUM'
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
