# 12-05の状態
from datetime import datetime
from flask import Flask, render_template, request, redirect, session,url_for
from flask_sqlalchemy import SQLAlchemy

import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# データベースの設定（PostgreSQL への接続）
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/vote_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = 'your_secret_key_here'


# 投票対象となるモデル（テーブル）を定義
class Candidate(db.Model):
    __tablename__ = 'candidate'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    votes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Candidate {self.name}>'
        # シリアルナンバーテーブルの定義
class SerialNumber(db.Model):
    __tablename__ = 'serial_numbers'
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(255), unique=True, nullable=False)
    used = db.Column(db.Boolean, default=False)

class LoveMessage(db.Model):
    __tablename__ = 'lovemessage'
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(255), db.ForeignKey('serial_numbers.serial_number'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())  # 修正箇所

    candidate = db.relationship('Candidate', backref='lovemessages')

@app.route('/')
def overview():
    return render_template('overview.html')  # プロジェクト概要ページを表示

@app.route('/verify_serial', methods=['POST'])
def verify_serial():
    serial_number = request.form['serial_number']
    serial_entry = SerialNumber.query.filter_by(serial_number=serial_number, used=False).first()

    logging.debug(f"[Verify Serial] Received serial_number: {serial_number}")
        
    if serial_entry:
        # 検証成功
        logging.debug(f"[Verify Serial] Found serial entry: {serial_entry}")
             # 検証成功、シリアルナンバーを「使用済み」にマーク
        serial_entry.used = True
            # シリアルナンバーをセッションに保存
        session['serial_number'] = serial_number
        db.session.commit()
        # シリアルナンバーが有効なら投票ページに進む
        return redirect(url_for('index'))
    else:
        # シリアルナンバーが無効または既に使用されている場合
        return render_template('overview.html', error="無効なシリアルナンバーです")
    


@app.route('/index')
def index():
    # 候補者を投票数が多い順に並べて取得
    candidates = Candidate.query.order_by(Candidate.votes.desc()).all()
    return render_template('index.html', candidate=candidates)

# 投票処理
@app.route('/vote', methods=['POST'])
def vote():
    serial_number = session.get('serial_number')  # セッションから取得
    candidate_id = request.form.get('candidate')
    session['candidate_id'] = candidate_id
    #投票したアイドルを取得
    candidate = Candidate.query.get(candidate_id)
    # 全てのアイドルのデータを取得（ランキング用）
    all_candidates = Candidate.query.order_by(Candidate.votes.desc()).all()
    
     # デバッグ用ログ
    logging.debug(f"[Vote Function] serial_number: {serial_number}, candidate_id: {candidate_id}")
     # 値が存在するか確認
    if not serial_number:
        logging.debug("[Vote Function] serial_number is missing!")

    if candidate:
        candidate.votes += 1  # 投票数を1増加
        lovemessage = LoveMessage(candidate_id=candidate_id, serial_number=serial_number)
        db.session.add(lovemessage)
        db.session.commit()  # データベースに変更を保存
    return render_template('results.html',candidate=candidate,all_candidates=all_candidates)  # 投票後にトップページにリダイレクト

@app.route('/results')
def results():
    candidates = Candidate.query.order_by(Candidate.votes.desc()).all()
    return render_template('results.html', candidate=candidates)

@app.route('/message', methods=['GET', 'POST'])
def send_message():
    # シリアルナンバーをセッションから取得（ログイン済みと仮定）
    serial_number = session.get('serial_number')# セッションから取得

    mes_info = db.session.query(SerialNumber, Candidate).join(
        Candidate, SerialNumber.candidate_id == Candidate.id
    ).filter(SerialNumber.serial_number == serial_number).first()

    if not mes_info:
        logging.debug("[Send Message] No matching candidate for the serial number.")
        return redirect(url_for('index'))  # 該当がない場合

    candidate_id = session.get('candidate_id')# セッションから取得
    # message = request.form.get('message')

        # メッセージをDBに保存
    new_message = LoveMessage(
        serial_number=serial_number,
        candidate_id=candidate_id
    )

     # 投票済みのアイドルを取得
    mes_info = db.session.query(SerialNumber, Candidate).join(Candidate, SerialNumber.candidate_id == Candidate.id).filter(SerialNumber.serial_number == serial_number).first()

    if not mes_info:
        return redirect(url_for('index'))  # 投票していない場合は別ページへリダイレクト

    candidate = mes_info[1]  # 投票したアイドル
    db.session.add(new_message)
    db.session.commit()

    return render_template('message.html', candidate=candidate)


if __name__ == '__main__':
    app.run(debug=True)
