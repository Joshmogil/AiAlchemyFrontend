
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, Request, Response
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession

import fastapi_users as fp

from app.db import get_async_session
from app.db import User, create_db_and_tables
from app.db import create_todo, get_todo, update_todo, get_todos, delete_todo

from app.schemas import UserCreate, UserRead, UserUpdate
from app.users import auth_backend, current_active_user, fastapi_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}

@app.post("/add", response_class=HTMLResponse)
async def post_add(request: Request, content: str = Form(...), session: AsyncSession = Depends(get_async_session)):
    session_key = request.cookies.get("session_key")
    todo = await create_todo(content=content, session_key=session_key, session=session)
    context = {"request": request, "todo": todo}
    return templates.TemplateResponse("todo/item.html", context)

@app.get("/edit/{item_id}", response_class=HTMLResponse)
async def get_edit(request: Request, item_id: int, session: AsyncSession = Depends(get_async_session)):
    todo = await get_todo(item_id= item_id, session= session)
    context = {"request": request, "todo": todo}
    return templates.TemplateResponse("todo/form.html", context)

@app.put("/edit/{item_id}", response_class=HTMLResponse)
async def put_edit(request: Request, item_id: int, content: str = Form(...), session: AsyncSession = Depends(get_async_session)):
    todo = await update_todo(item_id, content, session)
    context = {"request": request, "todo": todo}
    return templates.TemplateResponse("todo/item.html", context)

@app.delete("/delete/{item_id}", response_class=Response)
async def delete(item_id: int, session: AsyncSession = Depends(get_async_session)):
    await delete_todo(item_id, session)

@app.get("/user-home", response_class=HTMLResponse)
async def home(request: Request, session: AsyncSession = Depends(get_async_session)):
    session_key = request.cookies.get("session_key", uuid.uuid4().hex)
    todos = await get_todos(session_key=session_key, session=session)
    context = {
        "request": request,
        "todos": todos,
        "title": "Home"
    }
    response = templates.TemplateResponse("home.html", context)
    response.set_cookie(key="session_key", value=session_key, expires=259200)  # 3 days
    return response

@app.get("/authenticated-route")
@app.get("/crucible", response_class=HTMLResponse)
async def crucible(request: Request, session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    session_key = request.cookies.get("session_key", uuid.uuid4().hex)
    todos = await get_todos(session_key=session_key, session=session)
    context = {
        "request": request,
        "todos": todos,
        "title": "Home"
    }
    response = templates.TemplateResponse("home.html", context)
    response.set_cookie(key="session_key", value=session_key, expires=259200)  # 3 days
    return response

@app.get("/main", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.app:app", host="0.0.0.0", log_level="info")