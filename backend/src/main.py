import os,logging
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from .config.database import engine
from .routes import auth,dataset,config,trial,audit
from .middlewares.audit import AuditMiddleware
from .middlewares.request_id import RequestIdMiddleware
from .services.trial import queue
@asynccontextmanager
async def lifespan(app):
    if os.getenv('SEED_DEMO','true')=='true':
        try:
            from scripts.seed_demo import seed
            seed()
        except Exception:logging.exception('seed failed')
    yield
app=FastAPI(title='边缘遥测 LSM 合并工坊',lifespan=lifespan)
app.add_middleware(AuditMiddleware);app.add_middleware(RequestIdMiddleware)
@app.exception_handler(ValueError)
async def invalid(request:Request,exc):return JSONResponse(status_code=422,content={'detail':str(exc)})
@app.exception_handler(SQLAlchemyError)
async def db_error(request:Request,exc):
    logging.exception('database error');return JSONResponse(status_code=409,content={'detail':'数据库操作失败，请检查名称和引用后重试'})
@app.get('/health')
def health():
    with engine.connect() as c:c.execute(text('SELECT 1'))
    queue.ping();return {'status':'ok'}
for router in (auth.router,dataset.router,config.router,trial.router,audit.router):app.include_router(router)
