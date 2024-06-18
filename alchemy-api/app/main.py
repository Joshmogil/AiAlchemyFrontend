
import uuid

from fastapi import Depends
from fastapi import FastAPI, Form
from fastapi import Request, Response
from fastapi import HTTPException, Depends, status

from fastapi import FastAPI


from fastapi.responses import HTMLResponse

from fastapi.templating import Jinja2Templates

from fastapi.security import OAuth2PasswordBearer
from app.auth_bearer import JWTBearer


from app.utils import create_access_token,create_refresh_token,verify_password,get_hashed_password, token_required

from sqlalchemy.orm import Session

from app.database import Base
from app.database import SessionLocal
from app.database import engine
from app.models import create_todo
from app.models import delete_todo
from app.models import get_todo
from app.models import get_todos
from app.models import update_todo
from app.models import User, TokenTable
import app.models as models
import app.schemas as schemas


Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")






def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




@app.post("/register")
def register_user(user: schemas.UserCreate, session: Session = Depends(get_db)):
    existing_user = session.query(models.User).filter_by(email=user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    encrypted_password =get_hashed_password(user.password)

    new_user = models.User(username=user.username, email=user.email, password=encrypted_password )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return {"message":"user created successfully"}

@app.post('/login' ,response_model=schemas.TokenSchema)
def login(request: schemas.requestdetails, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email")
    hashed_pass = user.password
    if not verify_password(request.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    access=create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    token_db = models.TokenTable(user_id=user.id,  access_toke=access,  refresh_toke=refresh, status=True)
    db.add(token_db)
    db.commit()
    db.refresh(token_db)
    return {
        "access_token": access,
        "refresh_token": refresh,
    }

@app.get('/getusers')
def getusers(dependencies=Depends(JWTBearer()),session: Session = Depends(get_db)):
    user = session.query(models.User).all()
    return user

@app.post('/change-password')
def change_password(request: schemas.changepassword, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")
    
    if not verify_password(request.old_password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid old password")
    
    encrypted_password = get_hashed_password(request.new_password)
    user.password = encrypted_password
    db.commit()
    
    return {"message": "Password changed successfully"}

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