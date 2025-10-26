import json
import os
from flask import Blueprint, Flask, redirect, render_template, request, flash, jsonify, url_for, send_from_directory
from flask_login import login_required, current_user
import speech_recognition as sr
from .models import Note, User
from website import db
from werkzeug.utils import secure_filename

views = Blueprint("views", __name__)

# Set the upload folder outside of the static folder for security
UPLOAD_FOLDER = os.path.join("website","static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Max content length for file uploads
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit

# Helper function to check allowed file types
def allowed_file(filename):
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov', 'webp', 'webm', 
                          'pdf', 'docx', 'txt', 'csv', 'xlsx', 'pptx', 'raw', 'zip','heic','mp3','wav','m4a','mkv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@views.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html", user=current_user)

@views.route("/note", methods=["GET", "POST"])
@login_required
def note():
    if request.method == "POST":
        note = request.form.get("note")

        if len(note) < 1:
            flash("Note is too short!", category="error")
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash("Note added!", category="success")

    return render_template("note.html", user=current_user)

@views.route("/delete-note", methods=["POST"])
def delete_note():
    note = json.loads(request.data)
    noteId = note["noteId"]
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
            flash("Note Deleted!", category="success")
    return jsonify({})

# Voice Recognition Route
@views.route("/voice", methods=["GET", "POST"])
@login_required
def voice_recognition():
    transcript = ""
    error = ""

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file uploaded!", category="error")
        else:
            file = request.files["file"]
            if file.filename == "":
                flash("No selected file!", category="error")
            elif not file.filename.lower().endswith(".wav"):
                flash("Invalid file format! Please upload a .wav file.", category="error")
            else:
                try:
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(file) as source:
                        audio = recognizer.record(source)
                        transcript = recognizer.recognize_google(audio)
                    flash("Transcription successful!", category="success")
                except sr.UnknownValueError:
                    flash("Could not understand the audio.", category="error")
                except sr.RequestError:
                    flash("Speech recognition service unavailable.", category="error")

    return render_template("voice.html", transcript=transcript, error=error)



@views.route("/contact")
def contact():
    return render_template("contact.html", user=current_user)

# Photo Upload Route
@views.route("/upload-file", methods=["GET", "POST"])
@login_required
def upload_photo():
    user_upload_folder = os.path.join(UPLOAD_FOLDER, str(current_user.id))
    if not os.path.exists(user_upload_folder):
        os.makedirs(user_upload_folder)

    uploaded_files = os.listdir(user_upload_folder)

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file uploaded!", category="error")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            flash("No selected file!", category="error")
            return redirect(request.url)
        
        if len(file.filename) > 50:
            flash("File name too long!", category="error")
            return redirect(request.url)
        
        for f in uploaded_files:
            if f == file.filename:
                flash("File name already exists!", category="error")
                return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename).replace(' ', '_')
            file_path = os.path.join(user_upload_folder, filename)
            file.save(file_path)  
            flash("File uploaded successfully!", category="success")
            return redirect(url_for("views.upload_photo"))

        flash("File type not allowed!", category="error")
        return redirect(request.url)

    return render_template("upload_photo.html", user=current_user, uploaded_files=uploaded_files, uid=str(current_user.id))

# Delete Uploaded File Route
@views.route("/delete-file", methods=["GET"])
def delete_file():
    file_name = request.args.get("file")
    if file_name:
        user_upload_folder = os.path.join(UPLOAD_FOLDER, str(current_user.id))
        file_path = os.path.join(user_upload_folder, file_name)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            flash("File deleted successfully!", category="success")
        else:
            flash("File not found!", category="error")
    else:
        flash("No file specified for deletion.", category="error")
    return redirect(url_for("views.upload_photo"))

# Route to Download File
@views.route("/download-file/<filename>")
def download_file(filename):
    user_upload_folder = os.path.join(UPLOAD_FOLDER, str(current_user.id))
    file_path = os.path.join(user_upload_folder, filename)
    
    if os.path.exists(file_path):
        return send_from_directory(user_upload_folder, filename, as_attachment=True)
    else:
        flash("File not found or you do not have access to this file.", category="error")
        return redirect(url_for("views.upload_photo"))

# Route to View Uploaded File in a New Tab
@views.route("/view-file/<filename>")
def view_file(filename):
    user_upload_folder = os.path.join(UPLOAD_FOLDER, str(current_user.id))
    file_path = os.path.join(user_upload_folder, filename)

    if os.path.exists(file_path):
        return render_template("view_file.html", filename=filename, uid=str(current_user.id), download_url=url_for('views.download_file', filename=filename))
    else:
        flash("File not found or you do not have access to this file.", category="error")
        return redirect(url_for("views.upload_photo"))


@views.route("/about")
def about():
    return render_template("about.html", user=current_user)



@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # If the request method is POST, handle password change
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Validate if passwords match
        if new_password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('profile'))
        
        # Update password (assuming a function like 'update_password' exists)
        current_user.set_password(new_password)
        flash("Password updated successfully!", "success")
        return redirect(url_for('profile'))

    # Render the profile page with user data
    return render_template('profile.html')


@views.route("/404")
def page_not_found():
    return render_template("404.html", user=current_user)