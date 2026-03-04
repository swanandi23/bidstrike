from flask import render_template
from flask import Flask, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "bidstrike_secret"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bidstrike.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- MODELS ----------------

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    short_name = db.Column(db.String(10))
    budget_total = db.Column(db.Integer)
    budget_left = db.Column(db.Integer)
    total_points = db.Column(db.Integer, default=0)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    role = db.Column(db.String(10))
    base_price = db.Column(db.Integer)
    points = db.Column(db.Integer)
    overseas = db.Column(db.Boolean)
    sold = db.Column(db.Boolean, default=False)
    unsold = db.Column(db.Boolean, default=False)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer)
    team_id = db.Column(db.Integer)
    sold_price = db.Column(db.Integer)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))
    team_id = db.Column(db.Integer)

class AuctionState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_player_id = db.Column(db.Integer)

# ---------------- INIT DATABASE ----------------

@app.route("/init")
def init():

    db.drop_all()
    db.create_all()

    teams = [
        Team(name="Mumbai Indians", short_name="MI", budget_total=100, budget_left=100),
        Team(name="Chennai Super Kings", short_name="CSK", budget_total=100, budget_left=100),
        Team(name="Rajasthan Royals", short_name="RR", budget_total=100, budget_left=100),
        Team(name="Gujarat Titans", short_name="GT", budget_total=100, budget_left=100),
        Team(name="Punjab Kings", short_name="PBKS", budget_total=100, budget_left=100),
        Team(name="Royal Challengers Bangalore", short_name="RCB", budget_total=100, budget_left=100),
        Team(name="Kolkata Knight Riders", short_name="KKR", budget_total=100, budget_left=100),
        Team(name="Sunrisers Hyderabad", short_name="SRH", budget_total=100, budget_left=100)
    ]

    db.session.add_all(teams)
    db.session.commit()

    # ADMIN USER
    admin = User(username="admin", password="admin123", role="admin")
    db.session.add(admin)

    # TEAM USERS
    for t in Team.query.all():
        user = User(
            username=t.short_name.lower(),
            password="team123",
            role="team",
            team_id=t.id
        )
        db.session.add(user)

    db.session.commit()

    # ---------------- PLAYERS ----------------

    players = [

        # ---------------- WARM-UP ----------------

        Player(name="Vaibhav Sooryavanshi", role="BAT", base_price=1, points=22, overseas=False),
        Player(name="Ayush Mhatre", role="BAT", base_price=1, points=21, overseas=False),
        Player(name="Naveen-ul-Haq", role="BOWL", base_price=1, points=12, overseas=True),
        Player(name="Ramandeep Singh", role="AR", base_price=1, points=17, overseas=False),
        Player(name="Karthik Sharma", role="WK", base_price=1, points=17, overseas=False),
        Player(name="Sarfaraz Khan", role="WK", base_price=1, points=15, overseas=False),
        Player(name="Abdul Samad", role="AR", base_price=1, points=16, overseas=False),

        # ---------------- RISE PHASE ----------------

        Player(name="Devdutt Padikal", role="BAT", base_price=2, points=20, overseas=False),
        Player(name="Mayank Agarwal", role="BAT", base_price=2, points=18, overseas=False),
        Player(name="Angkrish Raghuwanshi", role="BAT", base_price=2, points=13, overseas=False),
        Player(name="Nitish Rana", role="BAT", base_price=2, points=14, overseas=False),
        Player(name="Manish Pandey", role="BAT", base_price=2, points=17, overseas=False),

        Player(name="Rahul Chahar", role="BOWL", base_price=3, points=14, overseas=False),
        Player(name="T Natrajan", role="BOWL", base_price=2, points=17, overseas=False),
        Player(name="Wanindu Hasaranga", role="BOWL", base_price=2, points=17, overseas=True),

        Player(name="Micheal Bracewell", role="AR", base_price=2, points=15, overseas=True),
        Player(name="Ben Stokes", role="AR", base_price=2, points=17, overseas=True),

        Player(name="Abhishek Porel", role="WK", base_price=2, points=22, overseas=False),
        Player(name="Ben Duckett", role="WK", base_price=2, points=18, overseas=True),

        # ---------------- MID EXPLOSION ----------------

        Player(name="Travis Head", role="BAT", base_price=4, points=25, overseas=True),
        Player(name="Shubman Gill", role="BAT", base_price=5, points=24, overseas=False),
        Player(name="Surya Kumar Yadav", role="BAT", base_price=5, points=25, overseas=False),

        Player(name="Hardik Pandya", role="AR", base_price=5, points=27, overseas=False),
        Player(name="Axar Patel", role="AR", base_price=5, points=25, overseas=False),

        Player(name="Kuldeep Yadav", role="BOWL", base_price=3, points=24, overseas=False),

        # ---------------- GRAND FINISH ----------------

        Player(name="Rohit Sharma", role="BAT", base_price=5, points=29, overseas=False),
        Player(name="Virat Kohli", role="BAT", base_price=5, points=30, overseas=False),

        Player(name="K L Rahul", role="WK", base_price=5, points=26, overseas=False),
        Player(name="Rishabh Pant", role="WK", base_price=5, points=23, overseas=False),
        Player(name="Phil Salt", role="WK", base_price=4, points=25, overseas=True),
        Player(name="Henrich Klassen", role="WK", base_price=3, points=25, overseas=True),
        Player(name="Jos Buttler", role="WK", base_price=4, points=24, overseas=True),

    ]

    db.session.add_all(players)
    db.session.commit()

    db.session.add(AuctionState(current_player_id=1))
    db.session.commit()

    return "BidStrike Initialized Successfully"


# ---------------- LOGIN ----------------

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        user = User.query.filter_by(username=request.form["username"]).first()

        if user and user.password == request.form["password"]:

            session["role"] = user.role
            session["team_id"] = user.team_id

            if user.role == "admin":
                return redirect("/admin")
            else:
                return redirect("/dashboard")

    return render_template("login.html")

# ---------------- ADMIN ----------------

@app.route("/admin")
def admin():

    state = AuctionState.query.first()
    player = Player.query.get(state.current_player_id)

    teams = Team.query.all()

    return render_template(
        "admin.html",
        player=player,
        teams=teams
    )

# ---------------- SELL ----------------

@app.route("/sell",methods=["POST"])
def sell():

    state=AuctionState.query.first()
    player=Player.query.get(state.current_player_id)

    team=Team.query.get(int(request.form["team_id"]))
    price=int(request.form["price"])

    if price<player.base_price:
        return "Price lower than base"

    team.budget_left-=price
    team.total_points+=player.points

    player.sold=True

    db.session.add(Purchase(player_id=player.id,team_id=team.id,sold_price=price))
    db.session.commit()

    return redirect("/present?sold=1")

# ---------------- UNSOLD ----------------

@app.route("/unsold",methods=["POST"])
def unsold():

    state=AuctionState.query.first()
    player=Player.query.get(state.current_player_id)

    player.unsold=True
    db.session.commit()

    return redirect("/next")

# ---------------- NEXT ----------------

@app.route("/next")
def next_player():

    state=AuctionState.query.first()
    state.current_player_id+=1
    db.session.commit()

    return redirect("/admin")

# ---------------- TEAM DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    team=Team.query.get(session["team_id"])

    purchases=Purchase.query.filter_by(team_id=team.id).all()

    players=""

    for p in purchases:
        pl=Player.query.get(p.player_id)
        players+=f"<li>{pl.name} - {p.sold_price} Cr</li>"

    return f"""
    <h1>{team.name}</h1>
    Budget Left: {team.budget_left}

    <h3>Players</h3>
    <ul>
    {players}
    </ul>
    """

# ---------------- PRESENTATION ----------------

@app.route("/present")
def present():

    state = AuctionState.query.first()
    player = Player.query.get(state.current_player_id)

    teams = Team.query.all()

    purchase = Purchase.query.filter_by(player_id=player.id).first()

    sold_team = None
    sold_price = None

    if purchase:
        sold_team = Team.query.get(purchase.team_id)
        sold_price = purchase.sold_price

    sold_flag = request.args.get("sold")
    unsold_flag = request.args.get("unsold")

    return render_template(
        "present.html",
        player=player,
        teams=teams,
        sold_team=sold_team,
        sold_price=sold_price,
        sold_flag=sold_flag,
        unsold_flag=unsold_flag
    )
if __name__ == "__main__":
    app.run(debug=True)