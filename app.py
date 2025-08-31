from flask import Flask, Response, render_template, send_from_directory, request, redirect, url_for, session, abort
import os
import json
from motion import MotionDetector
import notifier

with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

app = Flask(__name__)
app.secret_key = CONFIG.get('SECRET_KEY', 'change-me')

PHOTOS_DIR = 'photos'
VIDEOS_DIR = 'videos'
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

motion = MotionDetector()
motion.start()

def logged_in():
    return session.get('logged_in', False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '')
        p = request.form.get('password', '')
        if u == CONFIG.get('ADMIN_USERNAME') and p == CONFIG.get('ADMIN_PASSWORD'):
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error='نام کاربری یا رمز اشتباه است')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/stream')
def stream():
    if not logged_in():
        return redirect(url_for('login'))
    def gen():
        while True:
            frame = motion.get_jpeg()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    if not logged_in():
        return redirect(url_for('login'))
    photos = sorted(os.listdir(PHOTOS_DIR))[-50:][::-1] if os.path.isdir(PHOTOS_DIR) else []
    videos = sorted(os.listdir(VIDEOS_DIR))[-30:][::-1] if os.path.isdir(VIDEOS_DIR) else []
    return render_template('index.html', photos=photos, videos=videos)

@app.route('/photos/<path:filename>')
def serve_photo(filename):
    if not logged_in():
        return redirect(url_for('login'))
    return send_from_directory(PHOTOS_DIR, filename)

@app.route('/videos/<path:filename>')
def serve_video(filename):
    if not logged_in():
        return redirect(url_for('login'))
    return send_from_directory(VIDEOS_DIR, filename)

@app.route('/health')
def health():
    return {'status': 'ok'}

@app.route('/shutdown', methods=['POST'])
def shutdown():
    if not logged_in():
        abort(403)
    motion.stop()
    return {'stopped': True}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
