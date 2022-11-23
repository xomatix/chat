from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from chat.auth import login_required
from chat.db import get_db

bp = Blueprint('conv', __name__)

@bp.route('/')
@login_required
def index():
    db = get_db()
    conversations = []
    try:
        conversations = db.execute(
            'SELECT *'
            ' FROM conversation'
        ).fetchall()
    except Exception:
        pass
    print(conversations)
        
    return render_template('chat/index.html', conversations=conversations)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    
    if request.method == 'POST':
        nickname = request.form['nickname']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE nickname = ?', (nickname,)
        ).fetchone()

        if user is None or user['id'] == g.user['id']:
            error = 'Incorrect nickname.'
        
        if error is None:
            u = [g.user['nickname'], user['nickname']]
            u = f'\"{u}\"'
            print(f'\"{u}\"')

            db.execute(
                f'INSERT INTO conversation (users) VALUES ( {u} )'
            )
            db.commit()

            return redirect(url_for('conv.index'))
        
        flash(error)

    
    return render_template('chat/create.html')