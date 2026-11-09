from datetime import datetime
from flask_login import UserMixin
from apps.app import db
 
 
class Recuruitment(db.Model):
    """募集テーブル"""
    __tablename__ = "recuruitments"
 
    active_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"), nullable=False)
    title = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    photo = db.Column(db.LargeBinary, nullable=False)
    tag_id = db.Column(db.String(20), db.ForeignKey("recuruitment_tags.tag_id"), nullable=False)
    location_prefecture = db.Column(db.String(5), nullable=False)
    location_city = db.Column(db.String(10), nullable=False)
    location_detail = db.Column(db.String(30), nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)
    application_start_at = db.Column(db.DateTime, nullable=False)
    application_end_at = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    eligibility = db.Column(db.String(30), nullable=False)
    required_items = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    review_status = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
 
    user = db.relationship("User", back_populates="recruitments")
    likes = db.relationship("Like", back_populates="recruitment")
    search_histories = db.relationship("SearchHistory", back_populates="recruitment")
    participation_histories = db.relationship("ParticipationHistory", back_populates="recruitment")  # ← 追加！
    recruitment_histories = db.relationship("RecruitmentHistory", back_populates="recruitment")      # ← 追加！
    participants = db.relationship("Participants", back_populates="recruitment")
    view_histories = db.relationship("ViewHistory", back_populates="recruitment")
    tag = db.relationship("RecuruitmentTag", back_populates="recruitments")
    search_tags = db.relationship("SearchTag", back_populates="recruitment")
    entries = db.relationship("Entry", back_populates="recruitment")
 
class Like(db.Model):
    """お気に入りテーブル"""
    __tablename__ = "likes"
 
    favorite_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"), nullable=False)
    active_id = db.Column(db.String(20), db.ForeignKey("recuruitments.active_id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
 
    user = db.relationship("User", back_populates="likes")
    recruitment = db.relationship("Recuruitment", back_populates="favorites")
 
 
class SearchHistory(db.Model):
    """検索履歴テーブル"""
    __tablename__ = "search_histories"
 
    active_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"), nullable=False)
    title = db.Column(db.String(30))  # FK指定あり：参照先が特定できないため要確認
    description = db.Column(db.Text)
    photo = db.Column(db.String)
    tag_id = db.Column(db.String(20), db.ForeignKey("recuruitment_tags.tag_id"))
    location_prefecture = db.Column(db.String(5))
    location_city = db.Column(db.String(10))
    location_detail = db.Column(db.Text)
    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    capacity = db.Column(db.Integer)
    eligibility = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
 
    user = db.relationship("User", back_populates="search_histories")
 
 
class ParticipationHistory(db.Model):
    """参加履歴テーブル"""
    __tablename__ = "participation_histories"
 
    active_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"), nullable=False)
    title = db.Column(db.String(30), nullable=False)  # FK指定あり：参照先が特定できないため要確認
    description = db.Column(db.Text, nullable=False)
    tag_id = db.Column(db.String(20), db.ForeignKey("recuruitment_tags.tag_id"), nullable=False)
    location_prefecture = db.Column(db.String(5), nullable=False)
    location_city = db.Column(db.String(10), nullable=False)
    location_detail = db.Column(db.Text, nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)
    application_start_at = db.Column(db.DateTime, nullable=False)
    application_end_at = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    eligibility = db.Column(db.String(30), nullable=False)
    required_items = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    review_status = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    p_history_id = db.Column(db.String, primary_key=True)
 
    user = db.relationship("User", back_populates="participation_histories")
 
 
class RecuruitmentHistory(db.Model):
    """募集履歴テーブル"""
    __tablename__ = "recuruitment_histories"
 
    active_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"), nullable=False)
    title = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tag_id = db.Column(db.String(20), db.ForeignKey("recuruitment_tags.tag_id"), nullable=False)
    location_prefecture = db.Column(db.String(5), nullable=False)
    location_city = db.Column(db.String(10), nullable=False)
    location_detail = db.Column(db.Text, nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)
    application_start_at = db.Column(db.DateTime, nullable=False)
    application_end_at = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    eligibility = db.Column(db.String(30), nullable=False)
    required_items = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    review_status = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    r_history_id = db.Column(db.Integer, primary_key=True)
 
    user = db.relationship("User", back_populates="recruitment_histories")
 
 
class Participants(db.Model):
    """参加者テーブル"""
    __tablename__ = "participants"
 
    participant_id = db.Column(db.String(20), primary_key=True)
    activity_id = db.Column(db.String(20), db.ForeignKey("recuruitments.active_id"), nullable=False)
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"), nullable=False)
    participant_count = db.Column(db.Integer)
    varchar = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    applicant_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    update_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    cancel_at = db.Column(db.DateTime, nullable=False)
 
    user = db.relationship("User", back_populates="participations")
    recruitment = db.relationship("Recuruitment", back_populates="participants")
 
 
class ViewHistory(db.Model):
    """閲覧履歴テーブル"""
    __tablename__ = "view_histories"
 
    active_id = db.Column(db.String(20), db.ForeignKey("recuruitments.active_id"), nullable=False)
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"), nullable=False)
    apdate_at = db.Column(db.DateTime, nullable=False)
    id = db.Column(db.Integer, primary_key=True)
 
    user = db.relationship("User", back_populates="view_histories")
    recruitment = db.relationship("Recuruitment", back_populates="view_histories")
 
 
class RecuruitmentTag(db.Model):
    """タグ管理用テーブル"""
    __tablename__ = "recuruitment_tags"
 
    tag_id = db.Column(db.String(20), primary_key=True)
    tag_name = db.Column(db.String(20), nullable=False)
 
    recruitments = db.relationship("Recuruitment", back_populates="tag")
    search_tags = db.relationship("SearchTag", back_populates="tag")
 
 
class SearchTag(db.Model):
    """タグ検索用テーブル"""
    __tablename__ = "search_tags"
 
    id = db.Column(db.String(20), primary_key=True)
    tag_id = db.Column(db.String(20), db.ForeignKey("recuruitment_tags.tag_id"), nullable=False)
    recuritment_id = db.Column(db.String(20), db.ForeignKey("recuruitments.active_id"), nullable=False)
 
    tag = db.relationship("RecuruitmentTag", back_populates="search_tags")
    recruitment = db.relationship("Recuruitment", back_populates="search_tags")
 
 
class Title(db.Model):
    """称号テーブル"""
    __tablename__ = "titles"
 
    title_id = db.Column(db.String(20), primary_key=True)
    title_name = db.Column(db.String(20), nullable=False)
    title_explanation = db.Column(db.String, nullable=False)
 
 
class Entry(db.Model):
    """申込者テーブル"""
    __tablename__ = "entries"
 
    applicant_id = db.Column(db.String(20), primary_key=True)
    activity_id = db.Column(db.String(20), db.ForeignKey("recuruitments.active_id"), nullable=False)
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"), nullable=False)
    particpant_count = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(10), nullable=False)
    applicant_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    update_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    cansel_at = db.Column(db.DateTime, nullable=False)
 
    user = db.relationship("User", back_populates="entries")
    recruitment = db.relationship("Recuruitment", back_populates="entries")
 
 
class ActiveMessagae(db.Model):
    """活動用メッセージテーブル"""
    __tablename__ = "active_messagaes"
 
    user_id = db.Column(db.String(20), primary_key=True)
    message = db.Column(db.String(50))
    nickname = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    post_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    update_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
 
 
class ThanksPoint(db.Model):
    """サンクスポイントテーブル"""
    __tablename__ = "thanks_points"
 
    point_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"), nullable=False)
    activity_id = db.Column(db.String(20), db.ForeignKey("recuruitments.active_id"), nullable=False)
    record_id = db.Column(db.String(20), nullable=False)
    point_count = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
 
    user = db.relationship("User", back_populates="thanks_points")
 
 
class ContactHistory(db.Model):
    """お問い合わせ履歴テーブル"""
    __tablename__ = "contact_histories"
 
    contact_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey("users.user_id"), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    subject = db.Column(db.String(30), nullable=False)
    body = db.Column(db.Text, nullable=False)