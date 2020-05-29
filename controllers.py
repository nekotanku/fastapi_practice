from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPAuthorizationCredentials
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette.statues import HTTP_401_UNAUTHORIZED
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

def admin(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    #Basic認証で受け取った情報
    username = credentials.username
    password = hashlib.md5(credentials.password.encode()).hexdigest()
    #DBからユーザー名が一致するデータを取得
    user = db.session.query(User).filter(User.username == username).first()
    task = db.session.query(Task).filter(Task.user_id == user.id).all() if user is not None else []
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
    #問題ない場合管理者ページ
    return templates.TemplateResponse('admin.html',
        {'request':request,
        'user':user,
        'task':task})
