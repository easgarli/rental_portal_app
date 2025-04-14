from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from werkzeug.urls import url_parse

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'GET':
        role = request.args.get('role', 'tenant')
        if role not in ['tenant', 'landlord']:
            role = 'tenant'
        return render_template('auth/register.html', role=role)
    
    # Handle POST request
    data = request.form
    
    if User.query.filter_by(email=data['email']).first():
        flash('Email already registered', 'danger')
        return redirect(url_for('auth.register', role=data['role']))
        
    if data['password'] != data['confirm_password']:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('auth.register', role=data['role']))
        
    user = User(
        name=data['name'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        role=data['role']
    )
    
    db.session.add(user)
    db.session.commit()
    
    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    # Handle POST request
    data = request.form
    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password_hash(user.password, data['password']):
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    
    flash('Invalid email or password', 'danger')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home')) 