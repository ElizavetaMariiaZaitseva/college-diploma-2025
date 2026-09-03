from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diplom.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'Qwerty135A'
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    t_number = db.Column(db.String(12), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='user', lazy=True)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_tickets = db.Column(db.Integer, nullable=False)
    available_tickets = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    bookings = db.relationship('Booking', backref='event', lazy=True)


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tickets_count = db.Column(db.Integer, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Подтверждено')


with app.app_context():
    db.create_all()

    if not Event.query.first():
        events = [
            Event(name='Мультфильм "Ходячий замок"', total_tickets=100, available_tickets=100,
                  date='2025-06-06 10:00', price=1000.00, category='hz'),
            Event(name='Мультфильм"Мой сосед тоторо"', total_tickets=50, available_tickets=50,
                  date='2025-06-06 15:00', price=500.00, category='s5s'),
            Event(name='Концерт"Taylor Swift"', total_tickets=250, available_tickets=250,
                  date='2025-06-06 19:00', price=5000.00, category='tey3'),
            Event(name='Концерт"Billie Eilish"', total_tickets=250, available_tickets=250,
                  date='2025-09-15 19:00', price=10000.00, category='bey3'),
            Event(name='Концерт"The Weeknd"', total_tickets=50, available_tickets=50,
                  date='2025-08-25 21:00', price=5000.00, category='week3'),
            Event(name='Балет"Лебединое озеро"', total_tickets=50, available_tickets=50,
                  date='2025-07-30 12:00', price=7000.00, category='leb3'),
            Event(name='Балет"Жизель"', total_tickets=50, available_tickets=50,
                  date='2025-07-05 18:00', price=4000.00, category='jis3'),
            Event(name='Опера"Богема"', total_tickets=50, available_tickets=50,
                  date='2025-06-16 13:00', price=2000.00, category='bog3'),
            Event(name='Мультфильм"Унесенные призраками"', total_tickets=60, available_tickets=60,
                  date='2025-06-10 16:30', price=1500.00, category='ypriz3'),
            Event(name='Мультфильм"Небесный замок Лапута"', total_tickets=75, available_tickets=75,
                  date='2025-09-10 18:30', price=4000.00, category='neb3')
        ]
        db.session.bulk_save_objects(events)
        db.session.commit()


@app.route('/book/<int:event_id>', methods=['GET', 'POST'])
def book(event_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    event = Event.query.get_or_404(event_id)

    if request.method == 'POST':
        tickets_count = int(request.form['tickets_count'])

        if tickets_count > event.available_tickets:
            flash(f'Недостаточно билетов. Доступно только {event.available_tickets}', 'danger')
            return redirect(url_for('book', event_id=event_id))

        new_booking = Booking(
            event_id=event_id,
            user_id=user_id,
            tickets_count=tickets_count
        )

        event.available_tickets -= tickets_count

        try:
            db.session.add(new_booking)
            db.session.commit()
            flash('Бронирование успешно создано!', 'success')
            return redirect(url_for('my_account'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при бронировании: {str(e)}', 'danger')

    return render_template('booking.html', event=event)


menu = [{"name": "Главная", "url": "Main"},
        {"name": "О нас", "url": "About"}]


@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


with app.app_context():
    db.create_all()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('my_account'))
        else:
            flash('Неверный email или пароль', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not phone.startswith('+7') or len(phone) != 12 or not phone[1:].isdigit():
            flash('Номер телефона должен начинаться с +7 и содержать 11 цифр', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(t_number=phone).first():
            flash('Пользователь с таким номером телефона уже существует', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            t_number=phone,
            password=hashed_password
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при регистрации: {str(e)}', 'danger')

    return render_template('register.html')

@app.route('/account')
def account():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_date.desc()).all()

    return render_template('account.html', user=user, bookings=bookings)

@app.route('/events/<category>')
def show_events(category):
    events = Event.query.filter_by(category=category).all()
    return render_template('events2.html', events=events, category=category)

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('index'))



@app.route('/my_account')
def my_account():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('login'))

    bookings = Booking.query.filter_by(user_id=user.id).join(Event).all()

    return render_template('my_account.html',
                           user=user,
                           bookings=bookings)


@app.route('/check')
def check():
    return render_template('check.html')


@app.route('/c')
def c():
    return render_template('carousel.html')


@app.route('/test')
def t():
    return render_template('test2.html')


@app.route('/sob')
def sob():
    return render_template('sob.html')


@app.route('/theater')
def theater():
    return show_events('theater')


@app.route('/conc')
def conc():
    return render_template('conc.html')

@app.route('/teatr')
def teatr():
    return render_template('teatr.html')


@app.route('/hz')
def hz():
    return show_events('hz')

@app.route('/tey3')
def tey3():
    return show_events('tey3')

@app.route('/bey3')
def bey3():
    return show_events('bey3')

@app.route('/week3')
def week3():
    return show_events('week3')

@app.route('/leb3')
def leb3():
    return show_events('leb3')

@app.route('/neb3')
def neb3():
    return show_events('neb3')

@app.route('/jis3')
def jis3():
    return show_events('jis3')

@app.route('/bog3')
def bog3():
    return show_events('bog3')

@app.route('/s5s')
def s5s():
    return show_events('s5s')
@app.route('/sypr')
def sypr():
    return show_events('sypr')

@app.route('/conc1')
def conc1():
    return show_events('conc1')

@app.route('/ypriz3')
def ypriz3():
    return show_events('ypriz3')

@app.route('/tickethz')
def thz():
    return render_template('tickethod_z2.html')

@app.route('/hod')
def hod():
    return render_template('hod.html')

@app.route('/tey1')
def tey():
    return render_template('tey1.html')

@app.route('/bey1')
def bey():
    return render_template('bey1.html')

@app.route('/neb1')
def neb():
    return render_template('neb1.html')

@app.route('/week1')
def week():
    return render_template('week1.html')

@app.route('/leb1')
def leb():
    return render_template('leb1.html')


@app.route('/jis1')
def jis():
    return render_template('jis1.html')

@app.route('/bog1')
def bog():
    return render_template('bog1.html')

@app.route('/5ss')
def ss():
    return render_template('ss.html')

@app.route('/ypriz')
def ypriz():
    return render_template('ypriz2.html')



if __name__ == '__main__':
    app.run(debug=True)
