from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, flash
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
    game_records = db.relationship('GameRecord', backref='player', lazy=True)

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

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)  # 경기 날짜
    type = db.Column(db.String(50), nullable=False)  # 경기 종류 (예: 리그 경기, 친선 경기 등)
    opponent = db.Column(db.String(50), nullable=False)  # 상대팀 이름
    location = db.Column(db.String(100), nullable=True)  # 경기 장소
    player_records = db.relationship('GameRecord', backref='game', lazy=True)  # 경기별 선수 기록

class GameRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)  # 관련 경기 ID
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)  # 관련 선수 ID
    at_bats = db.Column(db.Integer, default=0)
    runs = db.Column(db.Integer, default=0)
    hits = db.Column(db.Integer, default=0)
    doubles = db.Column(db.Integer, default=0)
    triples = db.Column(db.Integer, default=0)
    home_runs = db.Column(db.Integer, default=0)
    rbis = db.Column(db.Integer, default=0)
    walks = db.Column(db.Integer, default=0)
    hit_by_pitch = db.Column(db.Integer, default=0)
    sacrifice_flies = db.Column(db.Integer, default=0)
    strikeouts = db.Column(db.Integer, default=0)

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
        # 입력값 검증
        game_date = request.form.get('game_date')
        game_type = request.form.get('game_type')
        opponent = request.form.get('opponent')
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
            at_bats = plate_appearances - walks - hit_by_pitch - sacrifice_flies
        except ValueError:
            # 처리 중 에러가 발생한 경우, 입력값 오류 응답
            return "Invalid input. Please enter numeric values.", 400
        
        # 게임 정보가 모두 제공되었는지 확인
        if not all([game_date, game_type, opponent]):
            return "Missing game information. Please provide date, type, and opponent.", 400
        
        # 날짜 형식을 검증하고 변환
        try:
            game_date = datetime.strptime(game_date, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD format.", 400
        
        # 새 게임 정보 생성 및 기록
        new_game = Game(date=game_date, type=game_type, opponent=opponent)
        db.session.add(new_game)
        db.session.flush()  # game 객체에 ID 할당
        
        # 새 경기 기록 생성 및 추가
        new_game_record = GameRecord(
            game_id=new_game.id,
            player_id=player_id,
            at_bats=at_bats,
            hits=hits,
            runs=runs,
            doubles=doubles,
            triples=triples,
            home_runs=home_runs,
            rbis=rbis,
            walks=walks,
            hit_by_pitch=hit_by_pitch,
            sacrifice_flies=sacrifice_flies,
            strikeouts=strikeouts
        )
        db.session.add(new_game_record)

        # 선수의 기존 기록 업데이트
        record = Record.query.filter_by(player_id=player_id).first()
        if record:
            record.at_bats += at_bats
            record.hits += hits
            record.runs += runs
            record.doubles += doubles
            record.triples += triples
            record.home_runs += home_runs
            record.rbis += rbis
            record.walks += walks
            record.hit_by_pitch += hit_by_pitch
            record.sacrifice_flies += sacrifice_flies
            record.strikeouts += strikeouts
        else:
            # 기존 기록이 없는 경우 새로 생성
            record = Record(
                player_id=player_id,
                at_bats=at_bats,
                hits=hits,
                runs=runs,
                doubles=doubles,
                triples=triples,
                home_runs=home_runs,
                rbis=rbis,
                walks=walks,
                hit_by_pitch=hit_by_pitch,
                sacrifice_flies=sacrifice_flies,
                strikeouts=strikeouts
            )
            db.session.add(record)
        
        # 데이터베이스 커밋
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return f"An error occurred while updating the records: {e}", 500

        # 성공적으로 업데이트 후 선수 프로필 페이지로 리디렉션
        return redirect(url_for('player', player_id=player_id))
    else:
        # GET 요청 처리: 기록 업데이트 폼을 표시
        return render_template('update_record.html', player=player, player_id=player.id)


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
        
        else:
            photo_url = None
        
        new_player = Player(name=name, grade=grade, position=position, back_number=back_number, photo=photo_url)
        db.session.add(new_player)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('add_player.html')

@app.route('/reset_record/<int:player_id>', methods=['POST'])

def reset_recent_game_record(player_id):
    # 해당 선수의 가장 최근 경기 기록을 조회
    recent_game_record = GameRecord.query.filter_by(player_id=player_id)\
        .order_by(GameRecord.id.desc()).first()


    if recent_game_record:
        # 기존 총 기록에서 최근 경기 기록을 빼기
        record = Record.query.filter_by(player_id=player_id).first()
        if record:
            record.at_bats = max(0, record.at_bats - recent_game_record.at_bats)
            record.hits = max(0, record.hits - recent_game_record.hits)
            record.runs = max(0, record.runs - recent_game_record.runs)
            record.doubles = max(0, record.doubles - recent_game_record.doubles)
            record.triples = max(0, record.triples - recent_game_record.triples)
            record.home_runs = max(0, record.home_runs - recent_game_record.home_runs)
            record.rbis = max(0, record.rbis - recent_game_record.rbis)
            record.walks = max(0, record.walks - recent_game_record.walks)
            record.hit_by_pitch = max(0, record.hit_by_pitch - recent_game_record.hit_by_pitch)
            record.sacrifice_flies = max(0, record.sacrifice_flies - recent_game_record.sacrifice_flies)
            record.strikeouts = max(0, record.strikeouts - recent_game_record.strikeouts)

        db.session.delete(recent_game_record)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return f"An error occurred while updating the records after deleting the recent game record: {e}", 500

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
    
@app.route('/delete_player/<int:player_id>', methods=['POST'])
def delete_player(player_id):
    # 해당 선수의 모든 경기 기록 삭제
    GameRecord.query.filter_by(player_id=player_id).delete()

    # 해당 선수의 총 기록 삭제
    Record.query.filter_by(player_id=player_id).delete()

    # 선수 삭제
    player = Player.query.get_or_404(player_id)
    db.session.delete(player)

    try:
        db.session.commit()
        flash('선수가 성공적으로 삭제되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'선수 삭제 중 오류가 발생했습니다: {e}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/')
def index():
    players = Player.query.all()
    return render_template('index.html', players=players)

@app.route('/player/<int:player_id>')
def player(player_id):
    player = Player.query.get_or_404(player_id)
    records = Record.query.filter_by(player_id=player_id).all()
    game_records = GameRecord.query.filter_by(player_id=player_id).all()
    # 날짜와 타율 데이터 준비
    dates = [game_record.game.date.strftime('%Y-%m-%d') for game_record in game_records]
    batting_averages = [game_record.batting_average for game_record in game_records]

    # 템플릿에 데이터 전달
    return render_template('player.html', player=player, records=records, game_records=game_records, dates=dates, batting_averages=batting_averages)



if __name__ == '__main__':
    app.run(debug=True)


