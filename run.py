#サーバを立ち上げるためだけの関数

from urls import app
import uvicorn

if __name__ == '__main__':
    uvicorn.run(app=app)
    #uvicorn.run(app=app, port=8888) にもできる
