
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, Request, Response


from fastapi import FastAPI


from fastapi.responses import HTMLResponse

from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine

from app.db import User, create_db_and_tables
from app.schemas import UserCreate, UserRead, UserUpdate
from app.users import auth_backend, current_active_user, fastapi_users

from app.models import create_todo ,delete_todo ,get_todo ,get_todos ,update_todo


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




def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    session_key = request.cookies.get("session_key", uuid.uuid4().hex)
    todos = get_todos(db, session_key)
    context = {
        "request": request,
        "todos": todos,
        "title": "Home"
    }
    response = templates.TemplateResponse("home.html", context)
    response.set_cookie(key="session_key", value=session_key, expires=259200)  # 3 days
    return response




@app.post("/add", response_class=HTMLResponse)
def post_add(request: Request, content: str = Form(...), db: Session = Depends(get_db)):
    session_key = request.cookies.get("session_key")
    todo = create_todo(db, content=content, session_key=session_key)
    context = {"request": request, "todo": todo}
    return templates.TemplateResponse("todo/item.html", context)


@app.get("/edit/{item_id}", response_class=HTMLResponse)
def get_edit(request: Request, item_id: int, db: Session = Depends(get_db)):
    todo = get_todo(db, item_id)
    context = {"request": request, "todo": todo}
    return templates.TemplateResponse("todo/form.html", context)


@app.put("/edit/{item_id}", response_class=HTMLResponse)
def put_edit(request: Request, item_id: int, content: str = Form(...), db: Session = Depends(get_db)):
    todo = update_todo(db, item_id, content)
    context = {"request": request, "todo": todo}
    return templates.TemplateResponse("todo/item.html", context)


@app.delete("/delete/{item_id}", response_class=Response)
def delete(item_id: int, db: Session = Depends(get_db)):
    delete_todo(db, item_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.app:app", host="0.0.0.0", log_level="info")