from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.responses import RedirectResponse

from mycalendar import MyCalendar
from datetime import datetime
from datetime import timedelta

import db
from models import User, Task
import hashlib
from auth import auth


import re  # new
pattern = re.compile(r'\w{4,20}')  # 任意の4~20の英数字を示す正規表現
pattern_pw = re.compile(r'\w{6,20}')  # 任意の6~20の英数字を示す正規表現
pattern_mail = re.compile(r'^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$') # e-mailの正規表現


app = FastAPI(
    title='FastAPIで作るToDoアプリケーション',
    description='FastAPIチュートリアル：FastAPIでToDoアプリを作る！',
    version='0.9 beta'
)

templates = Jinja2Templates(directory="templates")
jinja_env = templates.env

security = HTTPBasic()

def index(request: Request):
    return templates.TemplateResponse('index.html', {'request':request})

def admin(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    #Basic認証で受け取った情報
    username = auth(credentials)
    password = hashlib.md5(credentials.password.encode()).hexdigest()

    today = datetime.now()
    next_w = today + timedelta(days=7)
    #DBからユーザー名が一致するデータを取得
    user = db.session.query(User).filter(User.username == username).first()
    #データを取得後はセッションをクローズする
    db.session.close()
    #該当ユーザーがいない
    if user is None or user.password != password:
        error = 'ユーザー名かパスワードが間違っています'
        raise HTTPException(
            status_code = HTTP_401_UNAUTHORIZED,
            detail = error,
            headers={"WWW-Authenticate": "Basic"},
        )
    #task
    task = db.session.query(Task).filter(Task.user_id == user.id).all()
    db.session.close()

    cal = MyCalendar(username,
        {t.deadline.strftime('%Y%m%d'): t.done for t in task})


    cal = cal.formatyear(today.year, 4)

    task = [t for t in task if today <= t.deadline <= next_w]
    links = [t.deadline.strftime('/todo/'+username+'/%Y/%m/%d') for t in task]

    #問題ない場合管理者ページ
    return templates.TemplateResponse('admin.html',
        {'request':request,
        'user':user,
        'task':task,
        'links': links,
        'calendar': cal})



#非同期処理として処理する
async def register(request: Request):
    if request.method == 'GET':
        return templates.TemplateResponse('register.html',
            {'request': request,
            'username': '',
            'error':[]})

    if request.method == 'POST':
        data = await request.form()
        username = data.get('username')
        password = data.get('password')
        password_tmp = data.get('password_tmp')
        mail = data.get('mail')

        error = []
        tmp_user = db.session.query(User).filter(User.username == username).first()

        if tmp_user is not None:
            error.append('同じ名前のユーザーが存在します。')
        if password != password_tmp:
            error.append('入力したパスワードが一致しません')
        if pattern.match(username) is None:
            error.append('ユーザ名は4~20文字の半角英数字にしてください。')
        if pattern_pw.match(password) is None:
            error.append('パスワードは6~20文字の半角英数字にしてください。')
        if pattern_mail.match(mail) is None:
            error.append('正しくメールアドレスを入力してください。')

        if error:
            return templates.TemplateResponse('register.html',
                {'request':request,
                'username': username,
                'error': error})

        user = User(username, password, mail)
        db.session.add(user)
        db.session.commit()
        db.session.close()

        return templates.TemplateResponse('complete.html',
        {'request': request,
        'username': username})

def detail(request: Request, username, year, month, day, credentials: HTTPBasicCredentials=Depends(security)):
    #認証
    username_tmp = auth(credentials)
    #他のユーザーが訪問してきたら弾く
    if username_tmp != username:
        return RedirectResponse('/')
    #ログインユーザを取得
    user = db.session.query(User).filter(User.username == username).first()
    #ログインユーザのタスクを取得
    task = db.session.query(Task).filter(Task.user_id == user.id).all()
    db.session.close()

    #該当の日付と一致するするものだけのリストにする
    #月日は０埋め
    theday = '{}{}{}'.format(year, month.zfill(2), day.zfill(2))
    task = [t for t in task if t.deadline.strftime('%Y%m%d')==theday]

    return templates.TemplateResponse('detail.html',
        {'request': request,
         'username': username,
         'task': task,
         'year': year,
         'month': month,
         'day': day})


async def done(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    #認証
    username = auth(credentials)
    #ユーザー情報を取得
    user = db.session.query(User).filter(User.username == username).first()
    #ログインユーザーのタスクを取得
    task = db.session.query(Task).filter(Task.user_id == user.id).all()

    data = await request.form()
    t_dones = data.getlist('done[]')

    for t in task:
        if str(t.id) in t_dones:
            t.done = True

    db.session.commit()
    db.session.close()

    return RedirectResponse('/admin')

async def add(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    # 認証
    username = auth(credentials)

    # ユーザ情報を取得
    user = db.session.query(User).filter(User.username == username).first()

    # フォームからデータを取得
    data = await request.form()
    print(data)
    year = int(data['year'])
    month = int(data['month'])
    day = int(data['day'])
    hour = int(data['hour'])
    minute = int(data['minute'])

    deadline = datetime(year=year, month=month, day=day, hour=hour, minute=minute)

    # 新しくタスクを生成しコミット
    task = Task(user.id, data['content'], deadline)
    db.session.add(task)
    db.session.commit()
    db.session.close()

    return RedirectResponse('/admin')

def delete(request: Request, t_id, credentials: HTTPBasicCredentials = Depends(security)):
    #認証
    username = auth(credentials)
    #ログインユーザー情報取得
    user = db.session.query(User).filter(User.username == username).first()

    # 該当タスクを取得
    task = db.session.query(Task).filter(Task.id == t_id).first()
    # もしユーザIDが異なれば削除せずリダイレクト
    if task.user_id != user.id:
        return RedirectResponse('/admin')

    # 削除してコミット
    db.session.delete(task)
    db.session.commit()
    db.session.close()

    return RedirectResponse('/admin')

#WebAPI用実装
def get(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    username = auth(credentials)

    user = db.session.query(User).filter(User.username == username).first()

    task = db.session.query(Task).filter(Task.user_id == user.id).all()

    db.session.close()

    #returnの形式をJSONに
    task = [{
        'id': t.id,
        'content': t.content,
        'deadline': t.deadline.strftime('%Y-%m-%d %H:%M:%S'),
        'published': t.date.strftime('%Y-%m-%d %H:%M:%S'),
        'done': t.done,
        } for t in task]

    return task

async def insert(request: Request, content: str = Form(...),
    deadline: str = Form(...),
    credentials: HTTPBasicCredentials = Depends(security)):

    username = auth(credentials)

    user = db.session.query(User).filter(User.username == username).first()
    task = Task(user.id, content, datetime.strptime(deadline, '%Y-%m-%d_%H:%M:%S'))
    #task追加
    db.session.add(task)
    db.session.commit()
    #新しいtaskの取得
    task = db.session.query(Task).all()[-1]
    db.session.close()

    return{
        'id': task.id,
        'content': task.content,
        'deadline': task.deadline.strftime('%Y-%m-%d %H:%M:%S'),
        'published': task.date.strftime('%Y-%m-%d %H:%M:%S'),
        'done': task.done,
    }
