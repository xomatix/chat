from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from chat.auth import login_required
from chat.db import get_db
import json

bp = Blueprint('conv', __name__)

@bp.route('/')
@login_required
def index():
    db = get_db()
    conversations = []
    try:
        conversations = db.execute(
           f'SELECT * FROM conversation WHERE cuser = {g.user["id"]} OR suser = {g.user["id"]}'
        ).fetchall()
    except Exception:
        pass
    users = []
    uid = g.user['id']
    try:

        for item in conversations:
            t = item['cuser']
            if item['cuser'] == uid:
                t = item['suser']
            users.append(db.execute(
                f'SELECT nickname FROM user WHERE id = {t}'
            ).fetchall())
    
    except Exception:
        pass

    users = [item[0]['nickname'] for item in users]
    #c = users[0][0]['nickname']
    print(users, uid)
    
        
    return render_template('chat/index.html', conversations=conversations, users=users)

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
            u = user['id']

            db.execute(
                f'INSERT INTO conversation (cuser, suser) VALUES ( {g.user["id"]}, {u} )'
            )
            db.commit()

            return redirect(url_for('conv.index'))
        
        flash(error)

    
    return render_template('chat/create.html')

@bp.route('/conv/<id>', methods=('GET', 'POST'))
@login_required
def conversation(id):
    
    db = get_db()
    messages = []
    try:
        messages = db.execute(
            f'SELECT * FROM message WHERE conv = {id}'
        ).fetchall()
    except Exception:
        pass
    
    user = -1
    uid = g.user['id']
    try:

        item = messages[-1]
        t = item['cuser']
        if item['cuser'] == uid:
            t = item['suser']
        user = db.execute(
                f'SELECT nickname FROM user WHERE id = {t}'
        ).fetchall()
        user = user[0]['nickname']    
    
    except Exception:
        pass

    try:
        if request.method == 'POST':
            message = request.form['message']
            db = get_db()
            error = None
            db.execute(
                f'INSERT INTO message (author, value, date, conv) VALUES ( "{g.user["nickname"]}", "{message}", "{datetime.now()}", {id})'
            )
            db.commit()
            print(id, g.user["nickname"])
            return redirect(url_for('conv.conversation', id=id))
    except EOFError as e:
        print(e)
        pass

       # return redirect(url_for('conv.conversation', id=id))
        
    
    

    return render_template('chat/conversation.html', messages = messages, user=user, conv=id)

@bp.route('/msg/<conv>/<id>', methods=('GET', 'POST'))
@login_required
def delete(conv,id):
   
    msgid = -1
    db = get_db()
    try:
        msgid = db.execute(
            f'SELECT id FROM message WHERE author = "{g.user["nickname"]}" AND id = {id}'
        ).fetchone()
    except BufferError as e:
        print(e)
        pass

    print(msgid['id'], g.user["nickname"])
    print(type(msgid['id']), type(id))
    
    if int(msgid['id']) != int(id):
        return (url_for('conv.conversation', id=conv))
        #return msgid['id'] , id
    
    db.execute(
        f'DELETE FROM message WHERE id = {id}'
    )
    
    db.commit()
    flash("deleted")

    
    return redirect(url_for('conv.conversation', id=conv))