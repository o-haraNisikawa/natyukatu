import uuid
import os
import numpy as np
from pathlib import Path
from apps.app import db
from apps.crud.models import User
from apps.natyukatu.models import JON
from flask import Blueprint,render_template,current_app,send_from_directory
from apps.natyukatu.forms import JON
import pandas as pd
import joblib
from sqlalchemy import desc
from sklearn.feature_extraction.text import CountVectorizer

from flask import(
    Blueprint,
    current_app,
    render_template,
    send_from_directory,
    redirect,
    url_for,
    request,
    flash,
)
from flask_login import current_user,login_required
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError

dt = Blueprint("natyukatu",__name__,template_folder="templates")

# ==============================
# ① トップ・ユーザー登録
# ==============================

# TOP画面
@natyukatu.route("/")
def index():
    return render_template("natyukatu/top.html")


# 参加者ユーザー登録
@natyukatu.route("/users/new")
def create_user():
    return render_template("natyukatu/create_user.html")


# 募集者ユーザー登録
@natyukatu.route("/organizers/new")
def create_organizer():
    return render_template("natyukatu/create_organizer.html")


# パスワード再設定
@natyukatu.route("/password/reset")
def reset_password():
    return render_template("natyukatu/reset_password.html")


# ==============================
# ② 活動検索・閲覧
# ==============================

# 活動一覧・検索画面
@natyukatu.route("/activities")
def activities():
    return render_template("natyukatu/activities.html")


# 活動詳細画面
@natyukatu.route("/activities/<int:activity_id>")
def activity_detail(activity_id):
    return render_template(
        "natyukatu/activity_detail.html",
        activity_id=activity_id
    )


# お気に入り一覧画面
@natyukatu.route("/favorites")
@login_required
def favorites():
    return render_template("natyukatu/favorites.html")


# おすすめ活動画面
@natyukatu.route("/recommend")
@login_required
def recommend():
    return render_template("natyukatu/recommend.html")


# 特集活動画面
@natyukatu.route("/feature")
def feature():
    return render_template("natyukatu/feature.html")


# ==============================
# ③ 参加申込・参加履歴
# ==============================

# 参加申込画面
@natyukatu.route("/activities/<int:activity_id>/apply")
@login_required
def apply_activity(activity_id):
    return render_template(
        "natyukatu/apply.html",
        activity_id=activity_id
    )


# 参加申込完了画面
@natyukatu.route("/apply/complete")
@login_required
def apply_complete():
    return render_template("natyukatu/apply_complete.html")


# 参加履歴一覧画面
@natyukatu.route("/participations")
@login_required
def participations():
    return render_template("natyukatu/participations.html")


# 参加履歴詳細画面
@natyukatu.route("/participations/<int:participation_id>")
@login_required
def participation_detail(participation_id):
    return render_template(
        "natyukatu/participation_detail.html",
        participation_id=participation_id
    )


# 参加状況変更画面
@natyukatu.route("/participations/<int:participation_id>/status")
@login_required
def participation_status(participation_id):
    return render_template(
        "natyukatu/participation_status.html",
        participation_id=participation_id
    )


# ==============================
# ④ 募集管理
# ==============================

# 募集履歴一覧画面
@natyukatu.route("/recruitments")
@login_required
def recruitments():
    return render_template("natyukatu/recruitments.html")


# 新規募集登録画面
@natyukatu.route("/recruitments/new")
@login_required
def create_recruitment():
    return render_template("natyukatu/create_recruitment.html")


# 募集情報変更画面
@natyukatu.route("/recruitments/<int:recruitment_id>/edit")
@login_required
def edit_recruitment(recruitment_id):
    return render_template(
        "natyukatu/edit_recruitment.html",
        recruitment_id=recruitment_id
    )


# 申込受付管理画面
@natyukatu.route("/recruitments/<int:recruitment_id>/applicants")
@login_required
def applicants(recruitment_id):
    return render_template(
        "natyukatu/applicants.html",
        recruitment_id=recruitment_id
    )


# ==============================
# ⑤ マイページ・ユーザー情報
# ==============================

# マイページ
@natyukatu.route("/mypage")
@login_required
def mypage():
    return render_template("natyukatu/mypage.html")


# ユーザー情報変更画面
@natyukatu.route("/mypage/edit")
@login_required
def edit_profile():
    return render_template("natyukatu/edit_profile.html")


# 活動実績画面
@natyukatu.route("/mypage/records")
@login_required
def activity_records():
    return render_template("natyukatu/activity_records.html")


# ポイント・バッジ画面
@natyukatu.route("/mypage/points")
@login_required
def points():
    return render_template("natyukatu/points.html")


# ==============================
# ⑥ 活動用画面
# ==============================

# 活動中画面
@natyukatu.route("/activities/<int:activity_id>/participating")
@login_required
def participating(activity_id):
    return render_template(
        "natyukatu/participating.html",
        activity_id=activity_id
    )


# 活動終了後画面
@natyukatu.route("/activities/<int:activity_id>/complete")
@login_required
def activity_complete(activity_id):
    return render_template(
        "natyukatu/activity_complete.html",
        activity_id=activity_id
    )


# ==============================
# ⑦ 通知・メッセージ
# ==============================

# 通知一覧画面
@natyukatu.route("/notifications")
@login_required
def notifications():
    return render_template("natyukatu/notifications.html")


# 開催前通知画面
@natyukatu.route("/notifications/before")
@login_required
def before_notification():
    return render_template("natyukatu/before_notification.html")


# メッセージ画面
@natyukatu.route("/messages")
@login_required
def messages():
    return render_template("natyukatu/messages.html")


# ==============================
# ⑧ その他
# ==============================

# お問い合わせ画面
@natyukatu.route("/contact")
def contact():
    return render_template("natyukatu/contact.html")


# ランキング画面
@natyukatu.route("/ranking")
def ranking():
    return render_template("natyukatu/ranking.html")


# 管理者画面
@natyukatu.route("/admin")
@login_required
def admin():
    return render_template("natyukatu/admin.html")
