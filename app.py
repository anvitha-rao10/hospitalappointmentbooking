import os
import re
import smtplib
from flask import Flask, render_template, request, redirect, url_for, session, flash
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from models import db, Appointment, Admin, Doctor, AppointmentHistory, ContactQuery

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:anvitha@localhost/hospitaldb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def send_email(to_email, subject, body, reply_to=None):
    sender_email = 'hospitalbooking814@gmail.com'
    sender_password = 'scti refg hhyw sjyi'
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email
    if reply_to:
        msg['Reply-To'] = reply_to
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print("Email sending failed:", e)

HOSPITAL_OPEN_HOUR = 8
HOSPITAL_CLOSE_HOUR = 22
APPOINTMENT_DURATION = 30

@app.route('/', methods=['GET', 'POST'])
def index():
    doctors = Doctor.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        confirm = request.form.get('confirm')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        doctor = request.form.get('doctor')
        date = request.form.get('date')
        time = request.form.get('time')

        try:
            requested_time = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
        except Exception:
            flash("Invalid date/time format.")
            return redirect(url_for('index'))

        if confirm == 'no':
            flash("Appointment booking cancelled.")
            return redirect(url_for('index'))

        if confirm is None:
            # Check for duplicate appointments
            duplicates = Appointment.query.filter(
                Appointment.name == name,
                Appointment.email == email,
                Appointment.phone == phone,
                Appointment.doctor == doctor,
                Appointment.status == 'confirmed',
                db.func.date(Appointment.appointment_time) == requested_time.date()
            ).all()

            for appt in duplicates:
                diff = abs((appt.appointment_time - requested_time).total_seconds())
                if diff < 30 * 60:
                    return render_template('confirm_duplicate.html',
                                           name=name, email=email, phone=phone,
                                           doctor=doctor, date=date, time=time)

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.(com|in|org|net)$', email):
            flash("Invalid email format.")
            return redirect(url_for('index'))
        if not re.match(r'^\d{10}$', phone):
            flash("Phone number must be 10 digits.")
            return redirect(url_for('index'))
        if requested_time < datetime.now():
            flash("Cannot book past appointments.")
            return redirect(url_for('index'))
        if not (8 <= requested_time.hour < 22):
            flash("Appointments must be between 08:00 and 22:00.")
            return redirect(url_for('index'))

        same_day_appointments = Appointment.query.filter(
            Appointment.doctor == doctor,
            Appointment.status == 'confirmed',
            db.func.date(Appointment.appointment_time) == requested_time.date()
        ).all()

        new_start = requested_time
        new_end = new_start + timedelta(minutes=30)
        conflict = False
        for a in same_day_appointments:
            existing_start = a.appointment_time
            existing_end = existing_start + timedelta(minutes=30)
            if new_start < existing_end and existing_start < new_end:
                conflict = True
                break

        if not conflict:
            appointment_time = requested_time
            status = 'confirmed'
        else:
            last = Appointment.query.filter(
                Appointment.doctor == doctor,
                db.func.date(Appointment.appointment_time) == requested_time.date()
            ).order_by(Appointment.appointment_time.desc()).first()
            appointment_time = (last.appointment_time + timedelta(minutes=30)) if last else (requested_time + timedelta(minutes=30))
            status = 'waiting'

        new_appointment = Appointment(
            name=name, email=email, phone=phone,
            doctor=doctor, appointment_time=appointment_time, status=status
        )
        db.session.add(new_appointment)
        db.session.commit()

        subject = f"Appointment {status.capitalize()} - {doctor}"
        cancel_link = url_for('cancel_appointment', appointment_id=new_appointment.id, _external=True)
        body = f"""<p>Hi {name},</p>
<p>Your appointment with Dr. {doctor} is <strong>{status}</strong> at <strong>{appointment_time}</strong>.</p>
<p>Your appointment ID is: <strong>{new_appointment.id}</strong></p>
<p>If you wish to cancel the appointment, click the button below:</p>
<p><a href="{cancel_link}" style="padding: 10px 20px; background-color: #d9534f; color: white; text-decoration: none; border-radius: 5px;">Cancel Appointment</a></p>
<p>Thank you.</p>"""

        send_email(email, subject, body)

        if status == 'confirmed':
            flash("Appointment booked successfully!")
        else:
            flash("Added to waiting list. Please check your email for your appointment slot and reach the hospital 10 minutes prior to your appointment.")

        return redirect(url_for('index'))

    return render_template('index.html', doctors=doctors)

@app.route('/doctor_corner')
def doctor_corner():
    doctors = Doctor.query.filter_by(is_active=True).all()
    appointments_by_doctor = {}
    for doctor in doctors:
        appointments = Appointment.query.filter_by(doctor=doctor.name).order_by(Appointment.appointment_time).all()
        appointments_by_doctor[doctor.name] = {
            'specialization': doctor.specialization,
            'appointments': appointments
        }
    return render_template('doctor_corner.html', appointments_by_doctor=appointments_by_doctor)

@app.route('/cancel/<int:appointment_id>', methods=['GET'])
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = 'cancelled'
    db.session.commit()
    return f"""
        <h2>Appointment Cancelled</h2>
        <p>Your appointment with Dr. {appointment.doctor} scheduled on {appointment.appointment_time.strftime('%Y-%m-%d %H:%M')} has been successfully cancelled.</p>
    """


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        query = ContactQuery(name=name, email=email, message=message)
        db.session.add(query)
        db.session.commit()
        subject = f"New Contact Query from {name}"
        body = f"""Name: {name}
Email: {email}
Message:
{message}"""
        send_email('hospitalbooking814@gmail.com', subject, body, reply_to=email)
        flash("Thank you for contacting us, our staff will get back to you soon!.")
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin = Admin.login(request.form['username'], request.form['password'])
        if admin:
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials.")
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    appointments = Appointment.query.order_by(Appointment.appointment_time.desc()).all()
    return render_template('dashboard.html', appointments=appointments)

@app.route('/admin/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        name = request.form['name']
        specialization = request.form['specialization']
        if name and specialization:
            db.session.add(Doctor(name=name, specialization=specialization, is_active=True))
            db.session.commit()
            flash("Doctor added successfully.")
            return redirect(url_for('add_doctor'))
    doctors = Doctor.query.all()
    return render_template('add_doctor.html', doctors=doctors)

@app.route('/admin/toggle_doctor/<int:doctor_id>', methods=['POST'])
def toggle_doctor(doctor_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    doctor = Doctor.query.get(doctor_id)
    if doctor:
        doctor.is_active = not doctor.is_active
        db.session.commit()
        flash(f"Doctor '{doctor.name}' has been {'enabled' if doctor.is_active else 'disabled'}.")
    else:
        flash("Doctor not found.")
    return redirect(url_for('add_doctor'))

@app.route('/admin/add_admin', methods=['GET', 'POST'])
def add_admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if Admin.query.filter_by(username=username).first():
            flash('Admin with this username already exists.')
        else:
            new_admin = Admin(username=username, password=password)
            db.session.add(new_admin)
            db.session.commit()
            flash('New admin added successfully!')
        return redirect(url_for('add_admin'))
    admins = Admin.query.all()
    return render_template('add_admin.html', admins=admins)

@app.route('/admin/delete_admin/<int:admin_id>', methods=['POST'])
def delete_admin(admin_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    admin_to_delete = Admin.query.get_or_404(admin_id)
    if admin_to_delete.username == 'anvitha':
        flash("Default admin 'anvitha' cannot be deleted.")
        return redirect(url_for('add_admin'))
    db.session.delete(admin_to_delete)
    db.session.commit()
    flash('Admin deleted successfully!')
    return redirect(url_for('add_admin'))

@app.route('/admin/delete_doctor/<int:doctor_id>', methods=['POST'])
def delete_doctor(doctor_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    doctor = Doctor.query.get(doctor_id)
    if doctor:
        db.session.delete(doctor)
        db.session.commit()
        flash(f"Doctor '{doctor.name}' deleted successfully.")
    else:
        flash("Doctor not found.")
    return redirect(url_for('add_doctor'))

@app.route('/admin/delete/<int:appointment_id>', methods=['POST'])
def delete_appointment(appointment_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    appointment = Appointment.query.get(appointment_id)
    if appointment:
        history = AppointmentHistory(
            original_id=appointment.id,
            name=appointment.name,
            email=appointment.email,
            phone=appointment.phone,
            doctor=appointment.doctor,
            appointment_time=appointment.appointment_time,
            status=appointment.status
        )
        db.session.add(history)
        db.session.delete(appointment)
        db.session.commit()
        flash("Deleted & archived.")
    return redirect(url_for('dashboard'))

@app.route('/delete_all', methods=['POST'])
def delete_all():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    appointments = Appointment.query.all()
    for a in appointments:
        db.session.add(AppointmentHistory(
            original_id=a.id, name=a.name, email=a.email, phone=a.phone,
            doctor=a.doctor, appointment_time=a.appointment_time, status=a.status
        ))
        db.session.delete(a)
    db.session.commit()
    flash("All appointments archived.")
    return redirect(url_for('dashboard'))

@app.route('/admin/history')
def view_history():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    filter_status = request.args.get('status')
    if filter_status:
        history = AppointmentHistory.query.filter_by(status=filter_status).order_by(AppointmentHistory.deleted_at.desc()).all()
    else:
        history = AppointmentHistory.query.order_by(AppointmentHistory.deleted_at.desc()).all()
    return render_template('history.html', history=history, filter_status=filter_status)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Logged out.")
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
