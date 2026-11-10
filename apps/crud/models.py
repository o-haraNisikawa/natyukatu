from datetime import datetime
from apps.app import db,login_manager
from flask_login import  UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
 
from apps.natyukatu.models import Title
 
class User(db.Model, UserMixin):
    """ユーザーテーブル"""
    __tablename__ = "users"
 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    nickname = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(11), nullable=False)
    role = db.Column(db.Integer, nullable=False)
    create_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    update_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    title_id = db.Column(db.Integer,db.ForeignKey("titles.id"))  # FK
    tanks_point = db.Column(db.Integer, nullable=False)
    ranking_id = db.Column(db.Integer)
    group_name = db.Column(db.String(20), nullable=False)
    representative_name = db.Column(db.String(10), nullable=False)
    contact_email = db.Column(db.String(11), nullable=False)
    group_type = db.Column(db.String(20), nullable=False)
    users_title = db.relationship("Title", backref=db.backref("users",lazy=True))
    recruitments = db.relationship("Recruitment", back_populates="user")
    likes = db.relationship("Like", back_populates="user")
    search_histories = db.relationship("SearchHistory", back_populates="user")
    participation_histories = db.relationship("ParticipationHistory", back_populates="user")
    recruitment_histories = db.relationship("RecruitmentHistory", back_populates="user")
    participations = db.relationship("Participants", back_populates="user")
    view_histories = db.relationship("ViewHistory", back_populates="user")
    entries = db.relationship("Entry", back_populates="user")
    thanks_points = db.relationship("ThanksPoint", back_populates="user")

    @property
    def password(self):
        raise AttributeError("読み取り不可")
    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)
 
    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)
   
    def is_duplicate_email(self):
        return User.query.filter_by(email=self.email).first() is not None
   
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)