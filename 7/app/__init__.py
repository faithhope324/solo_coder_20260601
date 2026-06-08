import os
from flask import Flask

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(
    __name__,
    template_folder=os.path.join(basedir, 'templates'),
    static_folder=os.path.join(basedir, 'static')
)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['SIMILAR_FOLDER'] = os.path.join(basedir, 'static', 'similar')

from app import routes
