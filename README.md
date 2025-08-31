# Smart Security Cam (Flask + OpenCV + Telegram + Ngrok)

## Quick start
1) Edit `config.json` (strong password + Telegram bot token & chat id).
2) Install deps: `pip install -r requirements.txt`
3) Run: `python app.py`
4) Open: `http://127.0.0.1:5000` (login: admin / StrongPass123!)
5) Remote: run `ngrok http 5000` and use the public link.

## Notes
- Use CAMERA_INDEX 0/1/2 depending on your webcam.
- On Android, use Pydroid 3 for Python and Termux for ngrok.
