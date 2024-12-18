
from datetime import datetime
from flask import Flask, render_template, request, redirect, session,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 必須（Flaskのflash機能で必要）


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
    expires_at = db.Column(DateTime)

@app.route('/')
def overview():
    return render_template('overview.html')  # プロジェクト概要ページを表示

@app.route('/verify_serial', methods=['POST'])
def verify_serial():
    serial_number = request.form['serial_number']
    now = datetime.now()
    serial_entry = SerialNumber.query.filter_by(serial_number=serial_number, used=False).first()

    logging.debug(f"[Verify Serial] Received serial_number: {serial_number}")
        
    if serial_entry:
        if serial_entry.expires_at < now:
         return render_template('overview.html', error="期限切れのシリアルナンバーです")
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

    # すでに投票済みの場合はエラーメッセージを表示
    if session.get('voted', False):
        flash('既に投票済みです。')  # メッセージを保存
        return redirect(url_for('overview'))
    
    serial_number = session.get('serial_number')  # セッションから取得
    candidate_id = request.form.get('candidate')
    session['candidate_id'] = candidate_id
    #投票したアイドルを取得
    candidate = Candidate.query.get(candidate_id)

    
     # デバッグ用ログ
    logging.debug(f"[Vote Function] serial_number: {serial_number}, candidate_id: {candidate_id}")
     # 値が存在するか確認
    if not serial_number:
        logging.debug("[Vote Function] serial_number is missing!")

    if candidate:
        candidate.votes += 1  # 投票数を1増加
        db.session.commit()  # データベースに変更を保存
        # 全てのアイドルのデータを取得（ランキング用）
        all_candidates = Candidate.query.order_by(Candidate.votes.desc()).all()
        # セッションに投票済みフラグを設定
        session['voted'] = True
    return render_template('results.html',candidate=candidate,all_candidates=all_candidates)  # 投票後にトップページにリダイレクト

@app.route('/results')
def results():
    candidates = Candidate.query.order_by(Candidate.votes.desc()).all()
    return render_template('results.html', candidate=candidates)

if __name__ == '__main__':
    app.run(debug=True)
