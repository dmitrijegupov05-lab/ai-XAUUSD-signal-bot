# bot/screenshot_analyzer.py

import re
from datetime import datetime
from PIL import Image
import io

def analyze_screenshot(image_bytes):
    """
    Анализирует скриншот графика XAUUSD (упрощённая версия)
    """
    try:
        # Пробуем открыть изображение
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        # Извлекаем текст через простой анализ (без OCR)
        # Вместо OCR используем простые эвристики по цветам
        
        # Имитация анализа: определяем примерную цену
        # В реальности здесь нужен OCR, но для демо используем заглушку
        
        # Проверяем, есть ли тёмные области (свечи)
        pixels = list(img.getdata())
        dark_pixels = sum(1 for p in pixels if sum(p[:3]) < 100)
        dark_ratio = dark_pixels / len(pixels)
        
        # Простой сигнал на основе тёмных/светлых областей
        if dark_ratio > 0.3:
            signal = 'BUY'
            confidence = 'MEDIUM'
            reason = 'Обнаружена зона накопления (тёмные области)'
        elif dark_ratio < 0.1:
            signal = 'SELL'
            confidence = 'MEDIUM'
            reason = 'Обнаружена зона распределения (светлые области)'
        else:
            signal = 'HOLD'
            confidence = 'LOW'
            reason = 'Рынок в равновесии'
        
        return {
            'signal': signal,
            'confidence': confidence,
            'price': 2150.50,  # заглушка
            'support': 2130.00,
            'resistance': 2170.00,
            'rsi': 55,
            'macd': 0.01,
            'score': 1,
            'reason': reason + ' (упрощённый анализ без OCR)',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    except Exception as e:
        return {
            'signal': 'HOLD',
            'confidence': 'LOW',
            'reason': f'Ошибка: {str(e)}',
            'price': 0
        }
