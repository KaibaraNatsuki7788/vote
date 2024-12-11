# いらないと思うけど一応残しておく
from app import db, Candidate,app

def seed_candidates():
    candidates = ['平野紫耀', '永瀬廉', '髙橋海人']
    
    # アプリケーションコンテキストを開始する
    with app.app_context():
        for name in candidates:
            if not Candidate.query.filter_by(name=name).first():  # 候補者がDBに存在しない場合
                db.session.add(Candidate(name=name))
        
        db.session.commit()  # データベースに変更を保存
    print("候補者のデータが追加されました。")

if __name__ == "__main__":
    seed_candidates()

