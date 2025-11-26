import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Secret key for sessions, CSRF protection, etc.
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-key")

# Database URL from .env (Aiven Postgres)
db_uri = os.getenv("DATABASE_URL")
if not db_uri:
    raise RuntimeError("DATABASE_URL is not set in .env")

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ----------------- MODEL -----------------
class Application(db.Model):
    __tablename__ = "applications"

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

        # Basic guard – your HTML already marks fields as required
        if not all([email, full_name, gender, whatsapp, education, country, linkedin, domains]):
            error = "Please fill in all required fields and select at least one domain."
            return render_template("apply.html", error=error)

        # Create and save to DB
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

        # Redirect to thank-you page after successful submission
        return redirect(url_for("thank_you"))

    # GET request: render the form
    return render_template("apply.html")


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


# ----------------- MAIN ENTRY -----------------
if __name__ == "__main__":
    # Ensure the table exists
    with app.app_context():
        db.create_all()

    app.run(debug=True)
