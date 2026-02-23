from flask import Flask, request, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

app = Flask(__name__)
app.secret_key = "bidstrike_secret"

# ======================
# DATABASE CONFIG
# ======================

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bidstrike.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ======================
# MODELS
# ======================

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    budget_total = db.Column(db.Integer)
    budget_left = db.Column(db.Integer)
    total_points = db.Column(db.Integer, default=0)


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    role = db.Column(db.String(50))
    base_price = db.Column(db.Integer)
    points = db.Column(db.Integer)
    sold = db.Column(db.Boolean, default=False)


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer)
    team_id = db.Column(db.Integer)
    sold_price = db.Column(db.Integer)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))
    team_id = db.Column(db.Integer, nullable=True)


class AuctionState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_player_id = db.Column(db.Integer)
    round_number = db.Column(db.Integer, default=1)

# ======================
# INIT ROUTE
# ======================

@app.route("/init")
def init_db():
    db.create_all()

    if Team.query.first():
        return "Database already initialized!"

    teams = [
        Team(name="Mumbai Mavericks", budget_total=100, budget_left=100),
        Team(name="Delhi Dynamos", budget_total=100, budget_left=100),
        Team(name="Chennai Chargers", budget_total=100, budget_left=100),
        Team(name="Kolkata Kings", budget_total=100, budget_left=100)
    ]

    db.session.add_all(teams)
    db.session.commit()

    players = [
        Player(name="Virat X", role="Batsman", base_price=10, points=90),
        Player(name="Boom Boom Y", role="Bowler", base_price=8, points=85),
        Player(name="AllRounder Z", role="All-Rounder", base_price=12, points=95),
        Player(name="Power Hitter A", role="Batsman", base_price=9, points=88),
        Player(name="Spin Master B", role="Bowler", base_price=7, points=80),
        Player(name="Captain Cool C", role="All-Rounder", base_price=11, points=92)
    ]

    db.session.add_all(players)

    admin_user = User(
        username="admin",
        password=generate_password_hash("admin123"),
        role="admin"
    )

    db.session.add(admin_user)

    all_teams = Team.query.all()
    for team in all_teams:
        team_user = User(
            username=team.name.replace(" ", "").lower(),
            password=generate_password_hash("team123"),
            role="team",
            team_id=team.id
        )
        db.session.add(team_user)

    state = AuctionState(current_player_id=1, round_number=1)
    db.session.add(state)

    db.session.commit()

    return "BidStrike Initialized Successfully!"

# ======================
# LOGIN
# ======================

@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["role"] = user.role
            session["team_id"] = user.team_id
            return redirect("/dashboard")
        else:
            return "Invalid credentials!"

    return """
    <h2>BidStrike Login</h2>
    <form method="POST">
        Username:<br>
        <input type="text" name="username"><br><br>
        Password:<br>
        <input type="password" name="password"><br><br>
        <button type="submit">Login</button>
    </form>
    """

# ======================
# DASHBOARD
# ======================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if session["role"] == "admin":
        return redirect("/admin")

    team = Team.query.get(session["team_id"])
    purchases = Purchase.query.filter_by(team_id=team.id).all()

    player_list = []
    for purchase in purchases:
        player = Player.query.get(purchase.player_id)
        player_list.append(f"{player.name} - Bought for {purchase.sold_price}")

    return f"""
    <h1>{team.name} Dashboard</h1>
    <h3>Budget Left: {team.budget_left}</h3>
    <h3>Your Players:</h3>
    {'<br>'.join(player_list) if player_list else 'No players bought yet.'}
    <script>
        setTimeout(function(){{location.reload();}},3000);
    </script>
    """

# ======================
# ADMIN PANEL
# ======================

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/login")

    teams = Team.query.all()
    players = Player.query.filter_by(sold=False).all()
    state = AuctionState.query.first()
    current_player = Player.query.get(state.current_player_id)

    return f"""
    <h1>Admin Panel</h1>

    <h2>Current Player: {current_player.name}</h2>

    <a href="/next">Next Player</a><br><br>

    <form method="POST" action="/sell">
        Player ID:
        <input name="player_id"><br>
        Team ID:
        <input name="team_id"><br>
        Price:
        <input name="price"><br>
        <button type="submit">Sell</button>
    </form>

    <br><a href="/present">Open Presentation</a>
    """

@app.route("/sell", methods=["POST"])
def sell():
    if session.get("role") != "admin":
        return redirect("/login")

    player_id = int(request.form["player_id"])
    team_id = int(request.form["team_id"])
    price = int(request.form["price"])

    player = Player.query.get(player_id)
    team = Team.query.get(team_id)

    if player.sold:
        return "Already sold"

    if team.budget_left < price:
        return "Not enough budget"

    team.budget_left -= price
    team.total_points += player.points
    player.sold = True

    purchase = Purchase(
        player_id=player.id,
        team_id=team.id,
        sold_price=price
    )

    db.session.add(purchase)
    db.session.commit()

    return redirect("/admin")

@app.route("/next")
def next_player():
    if session.get("role") != "admin":
        return redirect("/login")

    state = AuctionState.query.first()
    total_players = Player.query.count()

    if state.current_player_id < total_players:
        state.current_player_id += 1
        db.session.commit()

    return redirect("/admin")

# ======================
# PRESENTATION
# ======================

@app.route("/present")
def present():
    state = AuctionState.query.first()
    player = Player.query.get(state.current_player_id)

    if not player:
        return "No player selected"

    status = "LIVE"
    if player.sold:
        status = "SOLD"

    return f"""
    <html>
    <body style="background:black;color:white;text-align:center;padding-top:50px;font-family:Arial;">
        <h1 style="font-size:60px;color:gold;">{player.name}</h1>
        <h2>{player.role}</h2>
        <h2>Base Price: {player.base_price}</h2>
        <h2>Points: {player.points}</h2>
        <h2 style="color:#22c55e;">{status}</h2>

        <script>
            setTimeout(function(){{location.reload();}},2000);
        </script>
    </body>
    </html>
    """

# ======================
# REVEAL
# ======================

@app.route("/reveal")
def reveal():
    teams = Team.query.order_by(Team.total_points.desc()).all()

    output = ""
    position = 1
    for team in teams:
        output += f"<h2>{position}. {team.name} - {team.total_points} Points</h2>"
        position += 1

    winner = teams[0].name if teams else "None"

    return f"""
    <body style="background:black;color:white;text-align:center;padding-top:100px;">
        <h1 style="color:gold;">Final Results</h1>
        {output}
        <h1 style="color:green;">Winner: {winner}</h1>
    </body>
    """

# ======================
# RUN
# ======================

if __name__ == "__main__":
    app.run(debug=True)