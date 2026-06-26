import os
import io
import base64
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from flask import Flask, render_template, send_from_directory, request, flash, redirect
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'LabOneTUSUR'
app.config['UPLOAD_FOLDER'] = 'static'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.config['RECAPTCHA_USE_SSL'] = False

# Настройки reCAPTCHA (тестовые ключи)
#app.config['RECAPTCHA_PUBLIC_KEY'] = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
#app.config['RECAPTCHA_PRIVATE_KEY'] = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'

# Настройки reCAPTCHA (реальные ключи)
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lf7ijYtAAAAAC_cnsUZRNJCHwjbnMEGJvQCuEZt'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6Lf7ijYtAAAAACuVuxVyyt9GoGEgGpTSUFysuMVA'

# Разрешённые расширения
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_static_folder():
    """Очищает директории static от всех файлов, кроме .keep"""
    folder = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        # Удаляем все файлы, кроме
        if os.path.isfile(filepath) and filename != '.keep':
            os.remove(filepath)

def shift_rectangular_rings(img_array, shift):
    """Выполняет циклический сдвиг пикселей по замкнутым прямоугольным рамкам"""
    h, w, c = img_array.shape
    result = img_array.copy()
    top, left, bottom, right = 0, 0, h - 1, w - 1

    while top < bottom and left < right:
        top_row = result[top, left:right + 1].copy()
        right_col = result[top + 1:bottom, right].copy()
        bottom_row = result[bottom, left:right + 1].copy()[::-1]
        left_col = result[top + 1:bottom, left].copy()[::-1]

        # Формируем замкнутый периметр рамки
        perimeter = np.concatenate([top_row, right_col, bottom_row, left_col])
        per_len = len(perimeter)
        if per_len == 0:
            break
        # Вычисляем сдвиг
        shift_mod = shift % per_len
        if shift_mod != 0:
            perimeter = np.roll(perimeter, shift_mod, axis=0)

        # Разбиваем периметр четыре стороны
        top_len = right - left + 1
        right_len = bottom - top - 1
        bottom_len = top_len
        left_len = right_len

        idx = 0
        result[top, left:right + 1] = perimeter[idx:idx + top_len]
        idx += top_len
        result[top + 1:bottom, right] = perimeter[idx:idx + right_len]
        idx += right_len
        result[bottom, left:right + 1] = perimeter[idx:idx + bottom_len][::-1]
        idx += bottom_len
        result[top + 1:bottom, left] = perimeter[idx:idx + left_len][::-1]

        # Переходим к следующей внутренней рамке
        top += 1
        left += 1
        bottom -= 1
        right -= 1

    return result

def generate_histogram(img_array):
    """Строит график распределения цветов RGB"""
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ('r', 'g', 'b')
    labels = ('Красный (R)', 'Зелёный (G)', 'Синий (B)')

    for i, color in enumerate(colors):
        hist, bins = np.histogram(img_array[:, :, i].ravel(), bins=256, range=(0, 256))
        ax.plot(bins[:-1], hist, color=color, alpha=0.7, linewidth=1.0, label=labels[i])
    ax.set_xlabel('Интенсивность')
    ax.set_ylabel('Количество пикселей')
    ax.set_title('График распределения цветов исходного изображения')
    ax.legend()
    ax.grid(True)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Проверяем капчу
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not recaptcha_response:
            flash('Пожалуйста, пройдите капчу')
            return redirect(request.url)

        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        data = {
            'secret': app.config['RECAPTCHA_PRIVATE_KEY'],
            'response': recaptcha_response
        }
        response = requests.post(verify_url, data=data)
        result = response.json()
        if not result.get('success'):
            flash('Ошибка проверки капчи. Попробуйте снова.')
            return redirect(request.url)

        # Проверяем выбран ли файл
        if 'image' not in request.files:
            flash('Файл не выбран')
            return redirect(request.url)

        file = request.files['image']
        if file.filename == '':
            flash('Файл не выбран')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Недопустимый формат файла. Разрешены: png, jpg, jpeg, gif, bmp')
            return redirect(request.url)

        # Получаем сдвиг
        shift_str = request.form.get('shift', '10')
        try:
            shift = int(shift_str)
            if shift < 1:
                flash('Сдвиг должен быть >= 1')
                return redirect(request.url)
        except ValueError:
            flash('Сдвиг должен быть целым числом')
            return redirect(request.url)

        # Обработка изображения
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Очищаем static перед сохранением
        clean_static_folder()

        # Сохраняем новый файл
        file.save(filepath)

        img = Image.open(filepath).convert('RGB')
        img_array = np.array(img)
        result_array = shift_rectangular_rings(img_array, shift)
        result_img = Image.fromarray(result_array)
        result_filename = 'result_' + filename
        result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
        result_img.save(result_path)

        # Строим гистограмму исходного изображения
        hist_b64 = generate_histogram(img_array)

        return render_template('result.html',
                               original=filename,
                               result=result_filename,
                               shift=shift,
                               histogram=hist_b64)

    # Показываем форму с капчей
    return render_template('index.html', recaptcha_site_key=app.config['RECAPTCHA_PUBLIC_KEY'])


@app.route('/static/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)