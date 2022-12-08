from datetime import datetime, timedelta
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

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
           f'SELECT * FROM conversation WHERE cuser = {g.user["id"]} OR suser = {g.user["id"]}'
        ).fetchall()
    except Exception:
        pass
    users = []
    uid = g.user['id']
    lastmsg = []
    print(conversations[-1]["cuser"])
    try:

        for item in conversations:
            t = item['cuser']
            if item['cuser'] == uid:
                t = item['suser']
            users.append(db.execute(
                f'SELECT id, nickname FROM user WHERE id = {t}'
            ).fetchall())

        for item in conversations:
            for user in users:
                if item['suser'] == user[0]['id'] or item['cuser'] == user[0]['id']:
                    lastmsg.append(db.execute(
                        f'SELECT value FROM message WHERE conv = {item["id"]}'
                    ).fetchall())
                    #print( len(lastmsg[-1]))
                    lastmsg[-1] = lastmsg[-1][-1]['value'] if len(lastmsg[-1]) > 0 else "no messages"
    
    except Exception:
        pass

    users = [item[0]['nickname'] for item in users]
    print(lastmsg)
    #lastmsg = [item[0]['value'] for item in lastmsg]

    print(users, uid, lastmsg)
    
        
    return render_template('chat/index.html', conversations=conversations, users=users, lastmsg=lastmsg)

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

    if request.method == 'POST':
        try:
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
            flash(e)


    messages = []
    try:
        messages = db.execute(
            f'SELECT * FROM message WHERE conv = {id}'
        ).fetchall()
        messages = messages[-50:]
        messages = [{k: item[k] for k in item.keys()} for item in messages]
        
    except Exception:
        pass

    
    for i in messages:
        i['date'] = datetime.strptime(i['date'], "%Y-%m-%d %H:%M:%S.%f")
        if i['date'] + timedelta(days=1) < datetime.now(): 
            i['date'] = datetime.strftime(i['date'], "%Y-%m-%d %H:%M")
        else:
            i['date'] = datetime.strftime(i['date'], "%H:%M")
        
        print(i['date'])
    
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

@bp.route('/<conv>', methods=('GET', 'POST'))
@login_required
def deleteconv(conv):
   
    convid = -1
    db = get_db()
    try:
        convid = db.execute(
            f'SELECT id FROM conversation WHERE cuser = "{g.user["id"]}" OR suser = "{g.user["id"]}" AND id = {conv}'
        ).fetchone()
    except BufferError as e:
        print(e)
        pass

    print(convid['id'], g.user["nickname"])
    print(type(convid['id']), type(conv))
    
    if int(convid['id']) != int(conv):
        return (url_for('conv.conversation', id=conv))
        #return convid['id'] , id
    
    db.execute(
        f'DELETE FROM conversation WHERE id = {conv}'
    )
    
    db.commit()

    db.execute(
        f'DELETE FROM message WHERE conv = {conv}'
    )
    
    db.commit()
    flash("deleted")

    
    return redirect(url_for('conv.index'))

@bp.route('/msg/<conv>/<id>/edit', methods=('GET', 'POST'))
@login_required
def edit(conv,id):
   
    msgid = -1
    db = get_db()
    try:
        msgid = db.execute(
            f'SELECT id FROM message WHERE author = "{g.user["nickname"]}" AND id = {id}'
        ).fetchone()
    except BufferError as e:
        print(e)
        pass
    
    if int(msgid['id']) != int(id):
        return (url_for('conv.conversation', id=conv))
    
    if request.method == 'POST':
        try:
            message = request.form['message']
            db.execute(
                f'UPDATE message SET value="{message}" WHERE id = {id}'
            )
            db.commit()
        except BufferError as e:
            flash(e)
        return redirect(url_for('conv.conversation', id=conv))
        
    
    message = db.execute(
            f'SELECT value FROM message WHERE author = "{g.user["nickname"]}" AND id = {id}'
        ).fetchone()
    
    return render_template("chat/edit.html", message=message)