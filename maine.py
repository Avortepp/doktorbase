from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import pycountry
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)
DATABASE = 'doctors.db'
UPLOAD_FOLDER = 'path/to/photos'  # Replace with your path
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Создание базы данных и таблицы
def create_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS doctors (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 full_name TEXT NOT NULL,
                 clinic_name TEXT,
                 clinic_email TEXT,
                 clinic_phone TEXT,
                 street_address TEXT NOT NULL,
                 city TEXT NOT NULL,
                 state TEXT NOT NULL,
                 postal_code TEXT NOT NULL,
                 country TEXT NOT NULL,
                 website TEXT,
                 photo TEXT,
                 specialization TEXT
                 )''')
    conn.commit()
    conn.close()
create_db()
def create_user_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 account TEXT NOT NULL,
                 password TEXT NOT NULL,
                 city TEXT NOT NULL,
                 birthdate DATE NOT NULL,
                 find_doctor BOOLEAN NOT NULL,
                 photo_path TEXT
                 )''')
    conn.commit()
    conn.close()
create_user_table()
@app.route('/update_profile', methods=['POST'])
def update_profile():
    user_data = {
        "user_name": request.form.get("user_name", "Имя пользователя"),
        "user_avatar": request.form.get("user_photo", "ссылка_на_фото"),
        "user_address": request.form.get("user_address", "Адрес пользователя"),
    }
    return redirect(url_for('look_doctor', **user_data))
@app.route('/')
def choose_registration_type():
    return render_template('index.html')

@app.route('/redirect_registration', methods=['POST'])
def redirect_registration():
    registration_type = request.form.get('registration_type')

    if registration_type == 'doctor':
        return redirect(url_for('doktor_register'))
    elif registration_type == 'user':
        return redirect(url_for('register_user'))
    else:
        # Обработка ошибки, если передан некорректный тип регистрации
        return redirect(url_for('choose_registration_type'))

@app.route('/doktor_register', methods=['GET', 'POST'])
def doktor_register():
    user_data = {
        "user_name": "Имя пользователя",
        "user_avatar": "ссылка_на_фото",
        "user_address": "Адрес пользователя",
    }

    if request.method == 'POST':
        doctor_data = request.form
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''INSERT INTO doctors (full_name, clinic_name, clinic_email, clinic_phone, street_address, city, state, postal_code, country, website, photo, specialization) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                     (doctor_data['full_name'], doctor_data['clinic_name'], doctor_data['clinic_email'], doctor_data['clinic_phone'],
                      doctor_data['street_address'], doctor_data['city'], doctor_data['state'], doctor_data['postal_code'],
                      doctor_data['country'], doctor_data['website'], doctor_data['photo'], doctor_data['specialization']))
        conn.commit()
        conn.close()

        # Refresh the user_data variable with the latest values
        user_data["user_name"] = doctor_data.get("full_name", user_data["user_name"])
        user_data["user_avatar"] = doctor_data.get("photo", user_data["user_avatar"])
        user_data["user_address"] = doctor_data.get("street_address", user_data["user_address"])

    # Retrieve the updated list of doctors
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM doctors")
    doctors = c.fetchall()
    conn.close()

    return render_template('doktor_register.html', countries=pycountry.countries, doctors=doctors, user_data=user_data)

@app.route('/user_register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        user_data = request.form
        photo = request.files['user_photo']

        if photo and allowed_file(photo.filename):
            # Убедитесь, что каталог для загрузки существует
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Создайте безопасное имя файла
            filename = secure_filename(f'{user_data["account"]}_photo.jpg')

            # Сохраните фото в каталог загрузки
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('''INSERT INTO users (account, password, city, birthdate, find_doctor, photo_path)
                         VALUES (?, ?, ?, ?, ?, ?)''', 
                         (user_data['account'], user_data['password'], user_data['city'], user_data['birthdate'], 'find_doctor' in user_data, filename))
            conn.commit()
            conn.close()
            return redirect(url_for('look_doctor'))
    
    return render_template('user_register.html')

# Функция для проверки, имеет ли файл разрешенное расширение
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}

@app.route('/look_doctor')
def look_doctor():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM doctors")
    doctors = c.fetchall()
    conn.close()

    user_data = {
        "user_name": "Имя пользователя",
        "user_avatar": "фото",
        "user_address": "Адрес пользователя",
    }

    return render_template('look_doctor.html', doctors=doctors, user_data=user_data)

if __name__ == '__main__':
    app.run(debug=True)