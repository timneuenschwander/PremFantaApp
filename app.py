from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
import webbrowser
import threading
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fantasy_pl.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Database Models
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    team = db.Column(db.String(50), nullable=False)
    points = db.Column(db.Integer, default=0)
    market_value = db.Column(db.Float, default=0.0)
    bid_value = db.Column(db.Float, default=0.0)
    role = db.Column(db.String(20), nullable=False, default="bench")  # 'start', 'bench', 'reserve'


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    manager_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Routes
@app.route('/')
def index():
    starters = Player.query.filter_by(role='start').all()
    bench = Player.query.filter_by(role='bench').all()
    reserves = Player.query.filter_by(role='reserve').all()

    return render_template(
        'index.html',
        starters=starters,
        bench=bench,
        reserves=reserves
    )

@app.route('/swap', methods=['POST'])
def swap_players():
    data = request.get_json()

    dragged_id = int(data['dragged_id'])
    target_id = int(data['target_id']) if data['target_id'] else None
    source_role = data['source_role']
    target_role = data['target_role']

    dragged_player = Player.query.get(dragged_id)
    if not dragged_player:
        return jsonify({'error': 'Dragged player not found'}), 404

    # Swap roles
    if target_id:
        target_player = Player.query.get(target_id)
        if not target_player:
            return jsonify({'error': 'Target player not found'}), 404

        # Swap roles
        dragged_player.role, target_player.role = target_player.role, dragged_player.role

    else:
        # Move dragged player into new role
        dragged_player.role = target_role

    db.session.commit()
    return jsonify({'message': 'Swap successful'})

@app.route('/lineup')
def lineup():
    players = Player.query.order_by(Player.points.desc()).limit(11).all()
    return render_template('lineup.html', players=players)

@app.route('/team-stats', methods=['GET', 'POST'])
def team_stats():
    if request.method == 'POST':
        for key in request.form:
            if key.startswith("player_"):
                player_id = int(key.split("_")[1])
                player = Player.query.get(player_id)
                player.name = request.form.get(f"name_{player_id}")
                player.position = request.form.get(f"position_{player_id}")
                player.team = request.form.get(f"team_{player_id}")
                player.market_value = float(request.form.get(f"market_{player_id}", 0))
                player.bid_value = float(request.form.get(f"bid_{player_id}", 0))
                player.role = request.form.get(f"role_{player_id}")
            db.session.commit()
        return redirect(url_for('team_stats'))


    players = Player.query.all()
    return render_template('team_stats.html', players=players)

@app.route('/gameplan')
def gameplan():
    return render_template('gameplan.html')

@app.route('/update-role', methods=['POST'])
def update_role():
    data = request.get_json()
    player_id = data.get('player_id')
    new_role = data.get('new_role')

    player = Player.query.get(player_id)
    if player:
        player.role = new_role
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

def seed_players():
    if Player.query.count() == 0:
        players = []

        
        starters = [
            ("Erling Haaland", "CF", "Man City", 250, 110.0, 150.0),
            ("Mohamed Salah", "CF, RW", "Liverpool", 230, 105.0, 145.0),
            ("Bukayo Saka", "RW", "Arsenal", 220, 102.0, 140.0),
            ("Bruno Fernandes", "CAM", "Man United", 210, 98.0, 135.0),
            ("Martin Ødegaard", "CM, CAM", "Arsenal", 205, 95.0, 130.0),
            ("Heung-min Son", "LM, CF", "Spurs", 200, 99.0, 132.0),
            ("Trent Alexander-Arnold", "RB", "Liverpool", 185, 85.0, 110.0),
            ("Kieran Trippier", "RB, LB", "Newcastle", 182, 83.0, 108.0),
            ("Virgil van Dijk", "CB", "Liverpool", 180, 82.0, 105.0),
            ("Alisson Becker", "GK", "Liverpool", 175, 78.0, 100.0),
            ("Joško Gvardiol", "CB, LB", "Man City", 170, 80.0, 98.0),
        ]

        for name, pos, team, pts, mv, bid in starters:
            players.append(Player(name=name, position=pos, team=team, points=pts, market_value=mv, bid_value=bid, role="start"))

        bench = [
            ("Gabriel Martinelli", "LW, LM", "Arsenal", 160, 77.0, 90.0),
            ("Julian Alvarez", "CF, CAM", "Man City", 158, 75.0, 88.0),
            ("James Maddison", "CAM", "Spurs", 156, 76.0, 89.0),
            ("Declan Rice", "CDM", "Arsenal", 154, 74.0, 87.0),
            ("Diogo Dalot", "RB, LB", "Man United", 152, 72.0, 85.0),
            ("Kai Havertz", "CM, CF", "Arsenal", 150, 71.0, 84.0),
            ("Ben Chilwell", "LB", "Chelsea", 148, 70.0, 82.0),
            ("Eberechi Eze", "CAM, LW", "Crystal Palace", 146, 69.0, 81.0),
            ("Robert Sánchez", "GK", "Chelsea", 144, 68.0, 80.0),
            ("Dominik Szoboszlai", "CM, RW", "Liverpool", 143, 67.0, 78.0),
            ("Mykhailo Mudryk", "LW", "Chelsea", 142, 66.0, 77.0),
            ("William Saliba", "CB", "Arsenal", 141, 65.0, 75.0),
            ("David Raya", "GK", "Arsenal", 140, 64.0, 74.0),
            ("Cristian Romero", "CB", "Spurs", 139, 63.0, 73.0),
            ("Matheus Cunha", "CF", "Wolves", 138, 62.0, 72.0),
        ]

        for name, pos, team, pts, mv, bid in bench:
            players.append(Player(name=name, position=pos, team=team, points=pts, market_value=mv, bid_value=bid, role="bench"))

        reserves = [
            ("Anthony Gordon", "LW, LM", "Newcastle", 130, 60.0, 68.0),
            ("Evan Ferguson", "CF", "Brighton", 128, 59.0, 66.0),
            ("Emiliano Martínez", "GK", "Aston Villa", 126, 58.0, 64.0),
            ("Lewis Dunk", "CB", "Brighton", 124, 57.0, 62.0),
        ]

        for name, pos, team, pts, mv, bid in reserves:
            players.append(Player(name=name, position=pos, team=team, points=pts, market_value=mv, bid_value=bid, role="reserve"))

        db.session.add_all(players)
        db.session.commit()


def open_browser():
    time.sleep(1)  # Ensure server starts before opening
    webbrowser.open_new("http://127.0.0.1:5000")

def index():
    starters = Player.query.filter_by(role='start').all()
    bench = Player.query.filter_by(role='bench').all()
    reserves = Player.query.filter_by(role='reserve').all()

    # Convert starters to a list of dicts
    starters_json = [
        {"id": p.id, "name": p.name, "position": p.position} for p in starters
    ]

    return render_template('index.html',
                           starters=starters_json,
                           bench=bench,
                           reserves=reserves)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_players()
    threading.Thread(target=open_browser).start()
    app.run(debug=True)