import os
import logging

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import text  # for raw SQL to create schema

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Secret key for sessions, CSRF protection, etc.
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-key")

# Database URL from .env (PostgreSQL)
db_uri = os.getenv("DATABASE_URL")
if not db_uri:
    raise RuntimeError("DATABASE_URL is not set in .env")

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Log SQL statements to the console (helpful for debugging)
app.config["SQLALCHEMY_ECHO"] = True

# Set up logging
logging.basicConfig(level=logging.INFO)

db = SQLAlchemy(app)


# ----------------- MODEL -----------------
class Application(db.Model):
    """
    applications table in ltlab_schema schema
    """
    __tablename__ = "applications"
    __table_args__ = {"schema": "ltlab_schema"}  # 👈 use your schema

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(32), nullable=False)
    whatsapp = db.Column(db.String(50), nullable=False)
    education = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    linkedin = db.Column(db.String(255), nullable=False)
    # comma-separated list from the "domains" checkboxes
    domains = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Application {self.id} {self.email}>"


# ----------------- ROUTES -----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/apply", methods=["GET", "POST"])
def apply():
    if request.method == "POST":
        # Read fields from the form
        email = request.form.get("email")
        full_name = request.form.get("fullName")
        gender = request.form.get("gender")
        whatsapp = request.form.get("whatsapp")
        education = request.form.get("college")
        country = request.form.get("country")
        linkedin = request.form.get("linkedin")
        domains_list = request.form.getlist("domains")  # from checkboxes
        domains = ",".join(domains_list) if domains_list else ""

        # Log what we got from the form
        app.logger.info(
            "FORM DATA -> email=%s, full_name=%s, gender=%s, whatsapp=%s, "
            "education=%s, country=%s, linkedin=%s, domains=%s",
            email,
            full_name,
            gender,
            whatsapp,
            education,
            country,
            linkedin,
            domains,
        )

        # Validation
        if not all([email, full_name, gender, whatsapp, education, country, linkedin, domains]):
            error = "Please fill in all required fields and select at least one domain."
            app.logger.warning("Validation failed. Error: %s", error)
            return render_template("apply.html", error=error)

        # Try inserting into DB
        try:
            application = Application(
                email=email,
                full_name=full_name,
                gender=gender,
                whatsapp=whatsapp,
                education=education,
                country=country,
                linkedin=linkedin,
                domains=domains,
            )

            db.session.add(application)
            db.session.commit()

            app.logger.info("✅ Application inserted successfully for email=%s", email)

        except Exception as e:
            db.session.rollback()
            app.logger.error("❌ Database error while inserting application: %s", e)
            # Show a friendly error page
            return "Internal server error while saving your application.", 500

        # Redirect to thank-you page after successful submission
        return redirect(url_for("thank_you"))

    # GET request: render the form
    return render_template("apply.html", error=None)


@app.route("/learn")
def learn():
    return render_template("learn.html")


@app.route("/research")
def research():
    return render_template("research.html")


@app.route("/jobs")
def jobs():
    return render_template("jobs.html")


@app.route("/thank-you")
def thank_you():
    return "<h2>✅ Thank you for applying to the LTLab Data Internship!</h2>"


from flask import Flask, render_template, request, redirect, url_for, session


app.secret_key = "change-me-in-production"  # required for session

# ---- LOGIN ROUTE ----
def authenticate_user(email: str, password: str):
    """Simple dummy authentication. Replace with DB lookup."""
    demo_user = {
        "email": "you@example.com",
        "password": "secret123",  # In production: hashed + salted!
        "name": "Demo User",
    }

    if email.lower() == demo_user["email"] and password == demo_user["password"]:
        return demo_user
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = authenticate_user(email, password)
        if not user:
            error = "Invalid email or password. Please try again."
        else:
            # Save user session
            session["user_id"] = user["email"]
            session["user_name"] = user["name"]
            session["remember_me"] = remember
            return redirect(url_for("home"))  # redirect to your homepage route

    return render_template("login.html", error=error)


# ---- LOGOUT ROUTE ----
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    # simple placeholder
    return "Forgot password page coming soon"



# ----------------- MAIN ENTRY -----------------
if __name__ == "__main__":
    with app.app_context():
        # 1️⃣ Make sure the schema exists BEFORE creating tables
        with db.engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS ltlab_schema;"))
            conn.commit()  # required in SQLAlchemy 2.x

        # 2️⃣ Create tables (now that the schema exists)
        db.create_all()

    # Run the server
    # Use host="0.0.0.0" if you want to access it from other machines on the network
    app.run(host="0.0.0.0", port=5000, debug=True)
