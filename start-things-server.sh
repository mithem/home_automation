export FLASK_APP=things_server.py
export FLASK_ENV=development # don't need gunicorn or similar, better yet, this offers auto-reload etc.
flask run -p 8001
