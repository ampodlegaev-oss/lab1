#!/usr/bin/env python3
"""
Автотесты для лабораторной работы №1 (Вариант 20)
"""

import sys
import os
import time
import subprocess
import numpy as np
import requests
from pathlib import Path


def test_imports():
    """Тест 1: Проверка импорта библиотек"""
    print("\nТест 1: Проверка импорта библиотек...")

    try:
        import flask
        import werkzeug
        import PIL
        import numpy
        import matplotlib
        import requests
        print("  Все библиотеки импортируются")
        return True
    except ImportError as e:
        print(f"  Ошибка импорта: {e}")
        return False


def test_shift_algorithm():
    """Тест 2: Проверка алгоритма на матрице 3х3"""
    print("\nТест 2: Алгоритм сдвига на 3х3...")

    # Создаём тестовое изображение 3х3
    test_data = np.array([
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ], dtype=np.uint8)

    # Конвертируем в RGB
    test_img = np.stack([test_data, test_data, test_data], axis=2)

    # Импортируем функцию shift_rectangular_rings
    from app import shift_rectangular_rings

    # Применяем сдвиг на 1
    result = shift_rectangular_rings(test_img, 1)

    # Ожидаемый результат для сдвига вправо
    expected = np.array([
        [4, 1, 2],
        [7, 5, 3],
        [8, 9, 6]
    ], dtype=np.uint8)

    if np.array_equal(result[:, :, 0], expected):
        print("  Тест 3х3 пройден")
        return True
    else:
        print("  Тест 3х3 не пройден")
        return False


def test_shift_by_perimeter():
    """Тест 3: Сдвиг на длину периметра"""
    print("\nТест 3: Сдвиг на длину периметра...")

    test_data = np.array([
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ], dtype=np.uint8)

    test_img = np.stack([test_data, test_data, test_data], axis=2)

    from app import shift_rectangular_rings

    # Периметр внешней рамки = 8
    result = shift_rectangular_rings(test_img, 8)

    if np.array_equal(result[:, :, 0], test_data):
        print("  Тест сдвига на периметр пройден")
        return True
    else:
        print("  Тест сдвига на периметр не пройден")
        return False


def test_center_pixel():
    """Тест 4: Центральный пиксель не должен меняться"""
    print("\nТест 4: Проверка центрального пикселя...")

    test_data = np.arange(1, 26).reshape(5, 5).astype(np.uint8)
    test_img = np.stack([test_data, test_data, test_data], axis=2)

    from app import shift_rectangular_rings

    result = shift_rectangular_rings(test_img, 10)

    if result[2, 2, 0] == 13:
        print("  Центральный пиксель не изменился")
        return True
    else:
        print("  Центральный пиксель изменился")
        return False


def test_server():
    """Тест 5: Проверка работы Flask-сервера"""
    print("\nТест 5: Проверка Flask-сервера...")

    # Запускаем сервер
    server = subprocess.Popen(
        [sys.executable, 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Время на запуск
    time.sleep(3)

    try:
        # Проверяем главную страницу
        resp = requests.get('http://127.0.0.1:5000/', timeout=5)

        if resp.status_code == 200:
            print("  Сервер запущен и отвечает (200 OK)")

            # Проверяем статику
            resp2 = requests.get('http://127.0.0.1:5000/static/', timeout=5)
            print(f"  Статика: {resp2.status_code}")

            server.terminate()
            return True
        else:
            print(f"  Сервер вернул: {resp.status_code}")
            server.terminate()
            return False

    except requests.ConnectionError:
        print("  Не удалось подключиться к серверу")
        server.terminate()
        return False
    except Exception as e:
        print(f"  Ошибка: {e}")
        server.terminate()
        return False


def main():
    """Запуск всех тестов"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЛАБОРАТОРНОЙ РАБОТЫ №1")
    print("Вариант 20: Сдвиг по прямоугольным рамкам")
    print("=" * 60)

    tests = [
        test_imports,
        test_shift_algorithm,
        test_shift_by_perimeter,
        test_center_pixel,
        test_server,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 60)
    print(f"Результат: {passed}/{total} тестов пройдено")

    if passed == total:
        print("Все тесты пройдены успешно!")
        return 0
    else:
        print("Некоторые тесты не пройдены")
        return 1


if __name__ == "__main__":
    sys.exit(main())