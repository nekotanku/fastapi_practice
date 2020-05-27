from fastapi import FastAPI
from starlette.requests import Request
from starlette.templating import Jinja2Templates


app = FastAPI(
    title='FastAPIで作るToDoアプリケーション',
    description='FastAPIチュートリアル：FastAPIでToDoアプリを作る！',
    version='0.9 beta'
)

templates = Jinja2Templates(directory="templates")
jinja_env = templates.env

def index(request: Request):
    return templates.TemplateResponse('index.html', {'request':request})

def admin(request:Request):
    return templates.TemplateResponse('admin.html',
    {'request':request,
    'username':'admin'})
