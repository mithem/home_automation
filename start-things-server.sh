export FLASK_APP=things_server.py
export FLASK_ENV=development # don't gunicorn or similar, but this offers auto-reload etc.
flask run -p 8001
