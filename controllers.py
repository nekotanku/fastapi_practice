from fastapi import FastAPI
from starlette.requests import Request
from starlette.templating import Jinja2Templates
import db
from models import User, Task

app = FastAPI(
    title='FastAPIで作るToDoアプリケーション',
    description='FastAPIチュートリアル：FastAPIでToDoアプリを作る！',
    version='0.9 beta'
)

templates = Jinja2Templates(directory="templates")
jinja_env = templates.env

def index(request: Request):
    return templates.TemplateResponse('index.html', {'request':request})

def admin(request: Request):
    #ユーザーとタスクを取得
    user = db.session.query(User).filter(User.username == 'admin').first()
    task = db.session.query(Task).filter(Task.user_id == user.id).all()
    #データを取得後はセッションをクローズする
    db.session.close()

    return templates.TemplateResponse('admin.html',
        {'request':request,
        'user':user,
        'task':task})
