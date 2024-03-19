from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///players.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(20), nullable=False, default='기본값')
    position = db.Column(db.String(30), nullable=True)
    back_number = db.Column(db.Integer, nullable=True)  # 등번호 필드 추가
    photo = db.Column(db.String(100), nullable=True)  # 사진 파일 경로를 저장하는 필드

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    at_bats = db.Column(db.Integer, nullable=False, default=0)
    runs = db.Column(db.Integer, nullable=False, default=0)
    hits = db.Column(db.Integer, nullable=False, default=0)
    doubles = db.Column(db.Integer, nullable=False, default=0)
    triples = db.Column(db.Integer, nullable=False, default=0)
    home_runs = db.Column(db.Integer, nullable=False, default=0)
    rbis = db.Column(db.Integer, nullable=False, default=0)
    walks = db.Column(db.Integer, nullable=False, default=0)
    hit_by_pitch = db.Column(db.Integer, nullable=False, default=0)
    sacrifice_flies = db.Column(db.Integer, nullable=False, default=0)
    strikeouts = db.Column(db.Integer, nullable=False, default=0)

    @property
    def batting_average(self):
        return self.hits / self.at_bats if self.at_bats > 0 else 0

    @property
    def on_base_percentage(self):
        on_base = self.hits + self.walks + self.hit_by_pitch
        total_bases = self.at_bats + self.walks + self.hit_by_pitch + self.sacrifice_flies
        return on_base / total_bases if total_bases > 0 else 0

    @property
    def slugging_percentage(self):
        single_hits = self.hits - (self.doubles + self.triples + self.home_runs)
        total_bases = single_hits + 2 * self.doubles + 3 * self.triples + 4 * self.home_runs
        return total_bases / self.at_bats if self.at_bats > 0 else 0

    @property
    def ops(self):
        return self.on_base_percentage + self.slugging_percentage

@app.route('/update_record/<int:player_id>', methods=['GET', 'POST'])
def update_record(player_id):
    player = Player.query.get_or_404(player_id)
    if request.method == 'POST':
        try:
            plate_appearances = int(request.form.get('plate_appearances', 0))
            hits = int(request.form.get('hits', 0))
            runs = int(request.form.get('runs', 0))
            doubles = int(request.form.get('doubles', 0))
            triples = int(request.form.get('triples', 0))
            home_runs = int(request.form.get('home_runs', 0))
            rbis = int(request.form.get('rbis', 0))
            walks = int(request.form.get('walks', 0))
            hit_by_pitch = int(request.form.get('hit_by_pitch', 0))
            sacrifice_flies = int(request.form.get('sacrifice_flies', 0))
            strikeouts = int(request.form.get('strikeouts', 0))
        except ValueError:
            return "Invalid input", 400

        record = Record.query.filter_by(player_id=player_id).first()
        if record is None:
            record = Record(player_id=player_id)
            db.session.add(record)

        record.at_bats = (record.at_bats or 0) + plate_appearances - (walks + sacrifice_flies + hit_by_pitch)
        record.hits = (record.hits or 0) + hits
        record.runs = (record.runs or 0) + runs
        record.doubles = (record.doubles or 0) + doubles
        record.triples = (record.triples or 0) + triples
        record.home_runs = (record.home_runs or 0) + home_runs
        record.rbis = (record.rbis or 0) + rbis
        record.walks = (record.walks or 0) + walks
        record.hit_by_pitch = (record.hit_by_pitch or 0) + hit_by_pitch
        record.sacrifice_flies = (record.sacrifice_flies or 0) + sacrifice_flies
        record.strikeouts = (record.strikeouts or 0) + strikeouts

        db.session.commit()
        return redirect(url_for('player', player_id=player_id))
    else:
        return render_template('update_record.html', player=player, player_id=player_id)

@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        name = request.form['name']
        grade = request.form.get('grade', '기본값')
        position = request.form['position']
        back_number = request.form.get('back_number')
        if back_number and back_number.isdigit():
            back_number = int(back_number)
        else:
            back_number = None

        photo = request.files['photo']
        photo_url = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            photo_url = os.path.join('uploads', filename)
        
        new_player = Player(name=name, grade=grade, position=position, back_number=back_number, photo=photo_url)
        db.session.add(new_player)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('add_player.html')

@app.route('/reset_record/<int:player_id>', methods=['POST'])
def reset_record(player_id):
    player = Player.query.get_or_404(player_id)
    record = Record.query.filter_by(player_id=player_id).first()
    
    if record:
        # 기록 필드를 0으로 초기화
        record.at_bats = 0
        record.hits = 0
        record.runs = 0
        record.doubles = 0
        record.triples = 0
        record.home_runs = 0
        record.rbis = 0
        record.walks = 0
        record.hit_by_pitch = 0
        record.sacrifice_flies = 0
        record.strikeouts = 0

        db.session.commit()
        
    return redirect(url_for('player', player_id=player_id))

@app.route('/edit_player/<int:player_id>', methods=['GET', 'POST'])
def edit_player(player_id):
    player = Player.query.get_or_404(player_id)
    if request.method == 'POST':
        player.name = request.form['name']
        player.grade = request.form.get('grade')
        player.position = request.form.get('position')
        back_number = request.form.get('back_number')
        if back_number and back_number.isdigit():
            player.back_number = int(back_number)

        photo = request.files['photo']
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            player.photo = os.path.join('uploads', filename)

        db.session.commit()
        return redirect(url_for('player', player_id=player.id))
    else:
        return render_template('edit_player.html', player=player)


@app.route('/')
def index():
    players = Player.query.all()
    return render_template('index.html', players=players)

@app.route('/player/<int:player_id>')
def player(player_id):
    player = Player.query.get_or_404(player_id)
    records = Record.query.filter_by(player_id=player_id).all()
    return render_template('player.html', player=player, records=records)

if __name__ == '__main__':
    app.run(debug=True)
