from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from website import db
from .models import User

admin = Blueprint('admin', __name__)

# Admin Panel Route (View All Users)
@admin.route('/admin', methods=['GET'])
@login_required
def admin_panel():
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', category='error')
        return redirect(url_for('views.home'))

    users = User.query.all()
    return render_template('admin_panel.html', users=users)

# Admin Route to Delete User
@admin.route('/admin/delete_user/<int:user_id>', methods=['GET'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        flash('You do not have permission to perform this action.', category='error')
        return redirect(url_for('views.home'))

    user = User.query.get(user_id)
    if user:
        # Prevent deleting yourself
        if user.id == current_user.id:
            flash('You cannot delete your own account.', category='error')
        else:
            db.session.delete(user)
            db.session.commit()
            flash('User deleted successfully!', category='success')
    else:
        flash('User not found!', category='error')

    return redirect(url_for('admin.admin_panel'))

# Admin Route to Promote User to Admin
@admin.route('/admin/promote_user/<int:user_id>', methods=['GET'])
@login_required
def promote_user(user_id):
    if not current_user.is_admin():
        flash('You do not have permission to perform this action.', category='error')
        return redirect(url_for('views.home'))

    user = User.query.get(user_id)
    if user:
        if user.role != 'admin':
            user.role = 'admin'
            db.session.commit()
            flash(f'User {user.first_name} has been promoted to admin!', category='success')
        else:
            flash('This user is already an admin.', category='warning')
    else:
        flash('User not found!', category='error')

    return redirect(url_for('admin.admin_panel'))

# Admin Route to Demote User to Regular User
@admin.route('/admin/demote_user/<int:user_id>', methods=['GET'])
@login_required
def demote_user(user_id):
    if not current_user.is_admin():
        flash('You do not have permission to perform this action.', category='error')
        return redirect(url_for('views.home'))

    user = User.query.get(user_id)
    if user:
        if user.role == 'admin':
            user.role = 'user'  # Demote to regular user
            db.session.commit()
            flash(f'User {user.first_name} has been demoted to regular user!', category='success')
        else:
            flash('This user is already a regular user.', category='warning')
    else:
        flash('User not found!', category='error')

    return redirect(url_for('admin.admin_panel'))
