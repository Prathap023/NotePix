import re
from flask import Blueprint, render_template, request, flash, redirect, session, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from website import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

# Login Route
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if user.is_admin():
                flash(f'Welcome back, Admin {user.first_name}!', category='success')
            else:
                flash(f'Welcome back, {user.first_name}!', category='success')
            print(user.id)
            
            login_user(user, remember=False)  # Ensure session expires on browser close
            session.permanent = False  # Make session non-permanent
            
            return redirect(url_for('views.home'))
        else:
            flash('Invalid email or password.', category='error')

    return render_template("login.html", user=current_user)


# Logout Route
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', category='success')
    return redirect(url_for('auth.login'))

# Sign-up Route
@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        first_name = request.form.get('firstName', '').strip()
        password1 = request.form.get('password1', '').strip()
        password2 = request.form.get('password2', '').strip()

        # Basic email validation
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash('Invalid email format.', category='error')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be at least 4 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be at least 2 characters.', category='error')
        elif password1 != password2:
            flash('Passwords do not match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            hashed_password = generate_password_hash(password1, method='pbkdf2:sha256', salt_length=16)
            new_user = User(email=email, first_name=first_name, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created successfully!', category='success')
            return redirect(url_for('views.home'))

    return render_template("signup.html", user=current_user)


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password').strip()
        new_password1 = request.form.get('new_password1').strip()
        new_password2 = request.form.get('new_password2').strip()

        # Check if the current password is correct
        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', category='error')
        elif len(new_password1) < 7:
            flash('New password must be at least 7 characters long.', category='error')
        elif new_password1 != new_password2:
            flash('New passwords do not match.', category='error')
        else:
            # Hash the new password and update the user's password
            hashed_password = generate_password_hash(new_password1, method='pbkdf2:sha256', salt_length=16)
            current_user.password = hashed_password
            db.session.commit()

            flash('Your password has been updated successfully.', category='success')
            return redirect(url_for('views.home'))

    return render_template('change_password.html', user=current_user)


# Route for Forgot Password
@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        first_name = request.form.get('first_name').strip()

        # Verify user by email and first name
        user = User.query.filter_by(email=email, first_name=first_name).first()

        if user:
            # Generate a password reset form URL
            return redirect(url_for('auth.reset_password', user_id=user.id))
        else:
            flash('User not found. Please check your email and first name.', category='error')

    return render_template('forgot_password.html')


@auth.route('/reset-password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        new_password1 = request.form.get('new_password1').strip()
        new_password2 = request.form.get('new_password2').strip()

        # Validate new password
        if len(new_password1) < 7:
            flash('New password must be at least 7 characters long.', category='error')
        elif new_password1 != new_password2:
            flash('Passwords do not match.', category='error')
        else:
            # Update the password
            hashed_password = generate_password_hash(new_password1, method='pbkdf2:sha256', salt_length=16)
            user.password = hashed_password
            db.session.commit()
            flash('Your password has been reset successfully.', category='success')
            return redirect(url_for('auth.login'))

    return render_template('reset_password.html', user=user)
