import pandas as pd
from flask import send_file
from flask import Flask, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "bidstrike_secret"

# ======================
# DATABASE CONFIG
# ======================

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bidstrike.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ======================
# DATABASE MODELS
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
    role = db.Column(db.String(20))  # "admin" or "team"
    team_id = db.Column(db.Integer, nullable=True)


# ======================
# ROUTES
# ======================

@app.route("/")
def home():
    return redirect("/login")


@app.route("/init")
def init_db():
    db.create_all()

    if Team.query.first():
        return "Database already initialized!"

    # Create Teams
    teams = [
        Team(name="Mumbai Mavericks", budget_total=100, budget_left=100),
        Team(name="Delhi Dynamos", budget_total=100, budget_left=100),
        Team(name="Chennai Chargers", budget_total=100, budget_left=100),
        Team(name="Kolkata Kings", budget_total=100, budget_left=100)
    ]

    db.session.add_all(teams)
    db.session.commit()

    # Create Players
    players = [
        Player(name="Virat X", role="Batsman", base_price=10, points=90),
        Player(name="Boom Boom Y", role="Bowler", base_price=8, points=85),
        Player(name="AllRounder Z", role="All-Rounder", base_price=12, points=95),
        Player(name="Power Hitter A", role="Batsman", base_price=9, points=88),
        Player(name="Spin Master B", role="Bowler", base_price=7, points=80),
        Player(name="Captain Cool C", role="All-Rounder", base_price=11, points=92)
    ]

    db.session.add_all(players)

    # Create Admin User
    admin_user = User(
        username="admin",
        password=generate_password_hash("admin123"),
        role="admin"
    )

    db.session.add(admin_user)

    # Create Team Users
    all_teams = Team.query.all()
    for team in all_teams:
        team_user = User(
            username=team.name.replace(" ", "").lower(),
            password=generate_password_hash("team123"),
            role="team",
            team_id=team.id
        )
        db.session.add(team_user)

    db.session.commit()

    return "BidStrike Initialized Successfully!"


# ======================
# LOGIN SYSTEM
# ======================

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
<html>
<head>
    <title>{team.name} Dashboard</title>
    <style>
        body {{
            background: #0f172a;
            color: white;
            font-family: Arial;
            padding: 40px;
        }}
        h1 {{
            color: gold;
        }}
        .card {{
            background: #1e293b;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>

    <h1>{team.name} Dashboard</h1>

    <div class="card">
        <h3>Budget Left: {team.budget_left}</h3>
    </div>

    <div class="card">
        <h3>Your Players:</h3>
        {'<br>'.join(player_list) if player_list else 'No players bought yet.'}
    </div>

    <a href="/logout">Logout</a>

    <script>
        setTimeout(function() {{
            location.reload();
        }}, 3000);
    </script>

</body>
</html>
"""


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ======================
# ADMIN PANEL
# ======================

@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    teams = Team.query.all()
    players = Player.query.filter_by(sold=False).all()

    return f"""
    <h1>⚡ BidStrike Admin Panel</h1>

    <form method="POST" action="/process_sale">

        <label>Player</label><br>
        <select name="player_id">
            {''.join([f'<option value="{p.id}">{p.name} | Points: {p.points}</option>' for p in players])}
        </select>
        <br><br>

        <label>Team</label><br>
        <select name="team_id">
            {''.join([f'<option value="{t.id}">{t.name} | Budget: {t.budget_left}</option>' for t in teams])}
        </select>
        <br><br>

        <label>Sold Price</label><br>
        <input type="number" name="price" required>
        <br><br>

        <button type="submit">SELL PLAYER</button>
    </form>

    <br><br>
    <a href="/reset">Reset Auction</a> |
    <a href="/logout">Logout</a>
    """


@app.route("/process_sale", methods=["POST"])
def process_sale():
    if session.get("role") != "admin":
        return redirect("/login")

    player_id = int(request.form["player_id"])
    team_id = int(request.form["team_id"])
    price = int(request.form["price"])

    player = Player.query.get(player_id)
    team = Team.query.get(team_id)

    if player.sold:
        return "Player already sold!"

    if team.budget_left < price:
        return "Not enough budget!"

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

    return f"""
<html>
<head>
    <title>SOLD</title>
    <style>
        body {{
            margin: 0;
            background: black;
            color: gold;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: Arial;
            flex-direction: column;
            animation: flash 0.5s alternate 6;
        }}

        h1 {{
            font-size: 80px;
            margin: 0;
        }}

        h2 {{
            font-size: 30px;
            margin-top: 20px;
            color: white;
        }}

        @keyframes flash {{
            from {{ background-color: black; }}
            to {{ background-color: #7f1d1d; }}
        }}
    </style>
</head>
<body>

    <h1>🔥 SOLD! 🔥</h1>
    <h2>{player.name} → {team.name}</h2>
    <h2>For {price}</h2>

    <script>
        setTimeout(function(){{
            window.location.href = "/admin";
        }}, 3000);
    </script>

</body>
</html>
"""
@app.route("/reveal")
def reveal_results():
    if session.get("role") != "admin":
        return redirect("/login")

    teams = Team.query.order_by(Team.total_points.asc()).all()

    team_names = [team.name for team in teams]
    team_points = [team.total_points for team in teams]

    return f"""
    <html>
    <head>
        <title>BidStrike Final Reveal</title>
        <style>
            body {{
                background: black;
                color: white;
                text-align: center;
                font-family: Arial;
                padding-top: 100px;
            }}

            h1 {{
                color: gold;
                font-size: 60px;
            }}

            .rank {{
                font-size: 35px;
                margin: 20px;
                display: none;
            }}

            .winner {{
                font-size: 55px;
                color: #22c55e;
                margin-top: 50px;
                display: none;
                animation: glow 1s infinite alternate;
            }}

            @keyframes glow {{
                from {{ text-shadow: 0 0 10px #22c55e; }}
                to {{ text-shadow: 0 0 25px #22c55e; }}
            }}
        </style>
    </head>
    <body>

        <h1>🏆 BIDSTRIKE FINAL REVEAL 🏆</h1>

        <div id="r4" class="rank"></div>
        <div id="r3" class="rank"></div>
        <div id="r2" class="rank"></div>
        <div id="winner" class="winner"></div>

        <script>
            let teams = {team_names};
            let points = {team_points};

            function revealRank(id, text, delay) {{
                setTimeout(function() {{
                    let el = document.getElementById(id);
                    el.innerHTML = text;
                    el.style.display = "block";
                }}, delay);
            }}

            revealRank("r4", "4th Place: " + teams[0] + " - " + points[0] + " pts", 1000);
            revealRank("r3", "3rd Place: " + teams[1] + " - " + points[1] + " pts", 3000);
            revealRank("r2", "2nd Place: " + teams[2] + " - " + points[2] + " pts", 5000);

            setTimeout(function() {{
                let win = document.getElementById("winner");
                win.innerHTML = "🎉 WINNER: " + teams[3] + " 🎉";
                win.style.display = "block";
            }}, 8000);
        </script>

    </body>
    </html>
    """

@app.route("/reset")
def reset_auction():
    if session.get("role") != "admin":
        return redirect("/login")

    Purchase.query.delete()

    teams = Team.query.all()
    for t in teams:
        t.budget_left = t.budget_total
        t.total_points = 0

    players = Player.query.all()
    for p in players:
        p.sold = False

    db.session.commit()

    return "Auction Reset Successful!"

@app.route("/export")
def export_results():
    if session.get("role") != "admin":
        return redirect("/login")

    teams = Team.query.order_by(Team.total_points.desc()).all()

    # Summary sheet
    summary_data = []
    for team in teams:
        summary_data.append({
            "Team": team.name,
            "Total Points": team.total_points,
            "Budget Left": team.budget_left
        })

    summary_df = pd.DataFrame(summary_data)

    file_path = "BidStrike_Results.xlsx"

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        # Individual team sheets
        for team in teams:
            purchases = Purchase.query.filter_by(team_id=team.id).all()

            team_data = []
            for purchase in purchases:
                player = Player.query.get(purchase.player_id)
                team_data.append({
                    "Player": player.name,
                    "Role": player.role,
                    "Points": player.points,
                    "Sold Price": purchase.sold_price
                })

            team_df = pd.DataFrame(team_data)
            team_df.to_excel(writer, sheet_name=team.name[:30], index=False)

    return send_file(file_path, as_attachment=True)

# ======================
# RUN SERVER
# ======================

if __name__ == "__main__":
    app.run(debug=True)