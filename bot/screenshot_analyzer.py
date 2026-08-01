# bot/screenshot_analyzer.py

import cv2
import numpy as np
import pytesseract
import re
from datetime import datetime

def analyze_screenshot(image_bytes):
    """
    Анализирует скриншот графика XAUUSD
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {
            'signal': 'HOLD',
            'confidence': 'LOW',
            'reason': 'Не удалось прочитать изображение',
            'price': 0
        }
    
    # Извлечение текста
    text = extract_text_from_image(img)
    
    # Поиск цен
    prices = extract_prices(text)
    
    # Поиск RSI и MACD
    rsi = extract_rsi(text)
    macd = extract_macd(text)
    
    # Поиск уровней
    support, resistance = find_support_resistance(img)
    
    # Генерация сигнала
    result = generate_signal_from_data(prices, support, resistance, rsi, macd)
    return result

def extract_text_from_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    try:
        text = pytesseract.image_to_string(gray, config='--psm 6')
        return text
    except:
        return ""

def extract_prices(text):
    pattern = r'\d{3,4}\.\d{2}'
    matches = re.findall(pattern, text)
    prices = []
    for m in matches:
        try:
            prices.append(float(m))
        except:
            pass
    return sorted(set(prices))

def extract_rsi(text):
    pattern = r'RSI[:\s]*(\d{1,3}\.?\d{0,2})'
    matches = re.search(pattern, text, re.IGNORECASE)
    if matches:
        try:
            return float(matches.group(1))
        except:
            return None
    return None

def extract_macd(text):
    pattern = r'MACD[:\s]*([-+]?\d+\.?\d*)'
    matches = re.search(pattern, text, re.IGNORECASE)
    if matches:
        try:
            return float(matches.group(1))
        except:
            return None
    return None

def find_support_resistance(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    
    y_positions = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y1 - y2) < 10:
                y_positions.append((y1 + y2) // 2)
    
    if not y_positions:
        return 0, 0
    
    y_positions = sorted(set(y_positions))
    if len(y_positions) >= 2:
        height = img.shape[0]
        price_min = 1900
        price_max = 2200
        price_range = price_max - price_min
        
        support = price_min + (y_positions[0] / height) * price_range
        resistance = price_min + (y_positions[-1] / height) * price_range
        return round(support, 2), round(resistance, 2)
    
    return 0, 0

def generate_signal_from_data(prices, support, resistance, rsi, macd):
    if not prices:
        return {
            'signal': 'HOLD',
            'confidence': 'LOW',
            'reason': 'Не удалось определить цены на скриншоте',
            'price': 0,
            'support': support,
            'resistance': resistance,
            'rsi': rsi or 0,
            'macd': macd or 0
        }
    
    current_price = prices[-1]
    score = 0
    reasons = []
    
    if support > 0 and current_price <= support * 1.002:
        score += 2
        reasons.append(f"Цена у поддержки ({support})")
    elif resistance > 0 and current_price >= resistance * 0.998:
        score -= 2
        reasons.append(f"Цена у сопротивления ({resistance})")
    
    if rsi:
        if rsi < 30:
            score += 2
            reasons.append(f"RSI={rsi:.1f} (перепроданность)")
        elif rsi > 70:
            score -= 2
            reasons.append(f"RSI={rsi:.1f} (перекупленность)")
        else:
            reasons.append(f"RSI={rsi:.1f} (нейтрально)")
    
    if macd:
        if macd > 0:
            score += 1
            reasons.append(f"MACD={macd:.3f} (бычий)")
        else:
            score -= 1
            reasons.append(f"MACD={macd:.3f} (медвежий)")
    
    if score >= 2:
        signal = 'BUY'
        confidence = 'HIGH' if score >= 3 else 'MEDIUM'
    elif score <= -2:
        signal = 'SELL'
        confidence = 'HIGH' if score <= -3 else 'MEDIUM'
    else:
        signal = 'HOLD'
        confidence = 'LOW'
    
    return {
        'signal': signal,
        'confidence': confidence,
        'price': current_price,
        'support': support,
        'resistance': resistance,
        'rsi': rsi if rsi else 0,
        'macd': macd if macd else 0,
        'score': score,
        'reason': ' | '.join(reasons) if reasons else 'Недостаточно данных',
        'time': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
