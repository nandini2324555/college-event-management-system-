import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Depends, Request, Form, Cookie, Query
from pydantic import BaseModel

from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

# ✅ FIXED IMPORTS (IMPORTANT)
import os
from pathlib import Path

from .database import engine, SessionLocal
from . import models

app = FastAPI()

@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=engine)
class Prompt(BaseModel):
    prompt: str
TEMPLATE_DIR = str(Path(__file__).resolve().parent / "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

ADMIN_SESSION_TOKEN = os.getenv("SECRET_KEY", "admin_token")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def send_confirmation_email(name: str, email: str, event_title: str, topics: str = ""):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    email_user = os.getenv("EMAIL_USERNAME")
    email_pass = os.getenv("EMAIL_PASSWORD")

    if email_user and email_pass:
        try:
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = email
            msg['Subject'] = "Event Registration Confirmation"

            topic_text = f"\nSelected Topics:\n{topics}" if topics else ""
            body = (
                f"Hello {name},\n\n"
                f"Your registration for '{event_title}' has been completed successfully.{topic_text}\n\n"
                f"Thank you for participating.\n\nRegards,\nCollege Event Management Team"
            )
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
            server.quit()
            print(f"Email sent to {email}")
        except Exception as e:
            print(f"Email error: {e}")
    else:
        print(f"[MOCK EMAIL] To: {email} | Registration confirmed for {event_title} | Topics: {topics}")

# ==================== LANDING PAGE ====================

@app.get("/", response_class=HTMLResponse)
def root(
    request: Request,
    db: Session = Depends(get_db),
    success: str = Query(None),
    error: str = Query(None),
    session: str = Cookie(None),
    search: str = Query(None)
):
    events_query = db.query(models.Event)
    if search:
        events_query = events_query.filter(models.Event.title.contains(search))
    events = events_query.all()

    events_with_count = []
    for event in events:
        reg_count = db.query(models.Registration).filter(models.Registration.event_id == event.id).count()
        events_with_count.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date,
            "category": event.category,
            "deadline": event.deadline,
            "registrations": reg_count,
        })

    return templates.TemplateResponse("index.html", {
        "request": request,
        "events": events_with_count,
        "success": success,
        "error": error,
        "session": session,
        "search": search,
    })

# ==================== STEP 1: REGISTRATION FORM ====================

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request, db: Session = Depends(get_db), session: str = Cookie(None)):
    events = db.query(models.Event).all()
    return templates.TemplateResponse("register.html", {
        "request": request,
        "events": events,
        "session": session,
    })

@app.post("/register")
async def register_submit(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    event_id = form.get("event_id")
    name = (form.get("name") or "").strip()
    email = (form.get("email") or "").strip()

    if not event_id or not name or not email:
        events = db.query(models.Event).all()
        return templates.TemplateResponse("register.html", {
            "request": request,
            "events": events,
            "error": "All fields are required. Please fill in your name, email, and select an event.",
        }, status_code=400)

    event = db.query(models.Event).filter(models.Event.id == int(event_id)).first()
    if not event:
        return RedirectResponse(url="/register?error=Event+not+found", status_code=303)

    return RedirectResponse(
        url=f"/event/{event.id}?from_reg=true&name={name}&email={email}",
        status_code=303
    )

# ==================== EVENT DETAILS (STEP 2) ====================

@app.get("/event/{event_id}", response_class=HTMLResponse)
def event_details(
    request: Request,
    event_id: int,
    db: Session = Depends(get_db),
    from_reg: str = Query(None),
    name: str = Query(None),
    email: str = Query(None),
    error: str = Query(None),
    success: str = Query(None),
    session: str = Cookie(None)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        return RedirectResponse(url="/", status_code=303)

    topics = db.query(models.Topic).filter(models.Topic.event_id == event_id).all()
    reg_count = db.query(models.Registration).filter(models.Registration.event_id == event_id).count()

    return templates.TemplateResponse("event_details.html", {
        "request": request,
        "event": event,
        "topics": topics,
        "registrations": reg_count,
        "session": session,
        "from_reg": from_reg,
        "student_name": name,
        "student_email": email,
        "error": error,
        "success": success,
    })

@app.post("/event/{event_id}/register")
async def register_from_event(
    request: Request,
    event_id: int,
    db: Session = Depends(get_db)
):
    form = await request.form()
    name = (form.get("name") or "").strip()
    email = (form.get("email") or "").strip()
    selected_topics = form.getlist("topics")

    if not name or not email:
        return RedirectResponse(
            url=f"/event/{event_id}?error=Name+and+email+are+required",
            status_code=303
        )

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        return RedirectResponse(url="/", status_code=303)

    if event.deadline:
        try:
            deadline_date = datetime.strptime(event.deadline, "%Y-%m-%d").date()
            if datetime.now().date() > deadline_date:
                return RedirectResponse(
                    url=f"/event/{event_id}?error=Registration+Closed+-+Deadline+has+passed",
                    status_code=303
                )
        except ValueError:
            pass

    topics_str = ", ".join(selected_topics) if selected_topics else "All topics"

    try:
        reg_data = RegistrationCreate(event_id=event_id, name=name, email=email)
    except Exception as e:
        return RedirectResponse(
            url=f"/event/{event_id}?error={str(e).replace(' ', '+')}",
            status_code=303
        )

    registration = models.Registration(
        event_id=reg_data.event_id,
        name=reg_data.name,
        email=reg_data.email,
        topics=topics_str,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    send_confirmation_email(reg_data.name, reg_data.email, event.title, topics_str)

    return RedirectResponse(
        url=f"/registration-success/{registration.id}",
        status_code=303
    )

# ==================== SUCCESS PAGE ====================

@app.get("/registration-success/{reg_id}", response_class=HTMLResponse)
def registration_success(
    request: Request,
    reg_id: int,
    db: Session = Depends(get_db),
    session: str = Cookie(None)
):
    registration = db.query(models.Registration).filter(models.Registration.id == reg_id).first()
    if not registration:
        return RedirectResponse(url="/", status_code=303)

    event = db.query(models.Event).filter(models.Event.id == registration.event_id).first()

    topic_list = []
    if registration.topics and registration.topics != "All topics":
        topic_list = [t.strip() for t in registration.topics.split(",")]

    return templates.TemplateResponse("success.html", {
        "request": request,
        "registration": registration,
        "event": event,
        "topic_list": topic_list,
        "session": session,
    })

# ==================== ADMIN LOGIN ====================

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = Query(None), session: str = Cookie(None)):
    if session == ADMIN_SESSION_TOKEN:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error,
    })

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    admin = db.query(models.Admin).filter(
        models.Admin.username == username,
        models.Admin.password == password
    ).first()

    if admin:
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session", value=ADMIN_SESSION_TOKEN)
        return response

    return RedirectResponse(url="/login?error=Invalid+username+or+password", status_code=303)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="session")
    return response

# ==================== ADMIN DASHBOARD ====================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), session: str = Cookie(None)):
    if session != ADMIN_SESSION_TOKEN:
        return RedirectResponse(url="/login", status_code=303)

    total_events = db.query(models.Event).count()
    total_registrations = db.query(models.Registration).count()

    events = db.query(models.Event).all()
    upcoming_events = sorted(events, key=lambda e: e.date)[:5]

    event_counts = []
    for ev in events:
        count = db.query(models.Registration).filter(models.Registration.event_id == ev.id).count()
        event_counts.append({"id": ev.id, "title": ev.title, "count": count})

    most_popular = max(event_counts, key=lambda x: x["count"]) if event_counts else {"id": 0, "title": "N/A", "count": 0}

    registrations = db.query(models.Registration).all()

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "total_events": total_events,
        "total_registrations": total_registrations,
        "upcoming_events": upcoming_events,
        "most_popular": most_popular,
        "event_counts": event_counts,
        "events": events,
        "registrations": registrations,
    })

# ==================== CREATE EVENT ====================

@app.post("/events")
def create_event(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    date: str = Form(...),
    category: str = Form("Workshop"),
    deadline: str = Form(None),
    db: Session = Depends(get_db),
    session: str = Cookie(None)
):
    if session != ADMIN_SESSION_TOKEN:
        return RedirectResponse(url="/login", status_code=303)

    try:
        event_data = EventCreate(title=title, description=description, date=date, category=category, deadline=deadline)
    except Exception as e:
        return RedirectResponse(url="/dashboard?error=" + str(e).replace(" ", "+"), status_code=303)

    new_event = models.Event(
        title=event_data.title,
        description=event_data.description,
        date=event_data.date,
        category=event_data.category,
        deadline=event_data.deadline,
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    predefined_topics = {
        "Technical": [
            "Introduction to Artificial Intelligence",
            "Machine Learning Basics Workshop",
            "Deep Learning Fundamentals",
            "Neural Networks Explained",
            "Computer Vision with OpenCV",
            "Natural Language Processing (NLP) Basics",
            "Generative AI & ChatGPT Applications",
            "AI in Real World Applications",
            "Model Building using Python",
            "AI Project Development Workshop",
        ],
        "Workshop": [
            "Python Basics for Beginners",
            "Python Data Types and Loops",
            "Functions and Object-Oriented Programming",
            "File Handling in Python",
            "Error Handling and Debugging",
            "Python for Data Analysis",
            "Working with Libraries (NumPy, Pandas)",
            "Mini Projects using Python",
            "Python Automation Basics",
            "Python for Web Development (Intro)",
        ],
        "Seminar": [
            "Introduction to Machine Learning",
            "Supervised vs Unsupervised Learning",
            "Linear Regression & Logistic Regression",
            "Decision Trees and Random Forest",
            "K-Means Clustering",
            "Data Preprocessing Techniques",
            "Model Training and Testing",
            "Feature Engineering Basics",
            "ML Model Evaluation Metrics",
            "Hands-on ML Project Session",
        ],
        "Sports": [
            "Cricket Tournament",
            "Football League",
            "Volleyball Championship",
            "Basketball Tournament",
            "Badminton Singles & Doubles",
            "Table Tennis Competition",
            "Kabaddi Match",
            "Athletics (100m, 200m, Relay Race)",
            "Tug of War",
            "Chess Tournament",
        ],
        "Cultural": [
            "Classical Dance Competition",
            "Western Dance Battle",
            "Singing Competition (Solo & Group)",
            "Battle of Bands",
            "Drama / Skit Performance",
            "Stand-up Comedy Show",
            "Fashion Walk / Ramp Walk",
            "Poetry & Story Writing Competition",
            "Painting & Poster Making Contest",
            "Photography Contest",
            "Talent Show Night",
        ],
    }

    for topic_title in predefined_topics.get(category, []):
        topic = models.Topic(event_id=new_event.id, title=topic_title)
        db.add(topic)
    db.commit()

    return RedirectResponse(url="/dashboard?success=Event+created+successfully!", status_code=303)

# ==================== DELETE EVENT ====================

@app.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    session: str = Cookie(None)
):
    if session != ADMIN_SESSION_TOKEN:
        return {"error": "Unauthorized"}

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        return {"error": "Event not found"}

    db.delete(event)
    db.commit()
    return {"message": "Event deleted"}

# ==================== EDIT EVENT ====================

@app.get("/edit/{event_id}", response_class=HTMLResponse)
def edit_event_page(request: Request, event_id: int, db: Session = Depends(get_db), session: str = Cookie(None)):
    if session != ADMIN_SESSION_TOKEN:
        return RedirectResponse(url="/login", status_code=303)
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("edit_event.html", {"request": request, "event": event})

@app.post("/edit/{event_id}")
def edit_event(
    request: Request,
    event_id: int,
    title: str = Form(...),
    description: str = Form(...),
    date: str = Form(...),
    category: str = Form("Workshop"),
    deadline: str = Form(None),
    db: Session = Depends(get_db),
    session: str = Cookie(None)
):
    if session != ADMIN_SESSION_TOKEN:
        return RedirectResponse(url="/login", status_code=303)

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        return RedirectResponse(url="/dashboard", status_code=303)

    try:
        event_update = EventUpdate(title=title, description=description, date=date, category=category, deadline=deadline)
    except Exception as e:
        return RedirectResponse(url=f"/edit/{event_id}?error={str(e).replace(' ', '+')}", status_code=303)

    if event_update.title:
        event.title = event_update.title
    if event_update.description:
        event.description = event_update.description
    if event_update.date:
        event.date = event_update.date
    if event_update.category:
        event.category = event_update.category
    if event_update.deadline is not None:
        event.deadline = event_update.deadline

    db.commit()
    return RedirectResponse(url="/dashboard?success=Event+updated+successfully!", status_code=303)

# ==================== API ENDPOINTS ====================

@app.get("/events")
def get_events(db: Session = Depends(get_db)):
    events = db.query(models.Event).all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "date": e.date,
            "category": e.category,
            "deadline": e.deadline,
        }
        for e in events
    ]

@app.get("/registrations")
def view_registrations(db: Session = Depends(get_db)):
    data = db.query(models.Registration).all()
    return [
        {
            "id": r.id,
            "event_id": r.event_id,
            "event_name": r.event.title if r.event else "Deleted Event",
            "name": r.name,
            "email": r.email,
            "topics": r.topics,
        }
        for r in data
    ]

@app.get("/create-admin")
def create_admin(db: Session = Depends(get_db)):
    existing = db.query(models.Admin).filter(models.Admin.username == ADMIN_USERNAME).first()
    if existing:
        return {"message": f"Admin '{ADMIN_USERNAME}' already exists"}
    admin = models.Admin(username=ADMIN_USERNAME, password=ADMIN_PASSWORD)
    db.add(admin)
    db.commit()
    return {"message": f"Admin '{ADMIN_USERNAME}' created successfully"}


@app.post("/ai-assistant")
def ai_assistant(data: Prompt):
    reply = ask_ollama(data.prompt)
    return {"response": reply}