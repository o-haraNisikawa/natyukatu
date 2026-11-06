from datetime import datetime
from uuid import uuid4 
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
    abort,
)

from apps.natyukatu.models import (
    Recuruitment,
    Like,
    Participants,
    ViewHistory,
    RecuruitmentTag,
    Entry,
    ActiveMessagae,
    ThanksPoint,
    Ranking,
    ContactHistory,
    ParticipationHistory,
    RecuruitmentHistory,
)


from apps.natyukatu.forms import (
    ParticipationForm,
    RecruitmentForm,
    ContactForm,
    FavoriteForm,
    MessageForm,
    RecruitmentDeleteForm,
    RecruitmentUpdateForm,
    HistoryUpdateForm,
    SearchForm,
    ApplicantDecisionForm,
    WithdrawalForm,
    UserUpdateForm,
)

from flask_login import current_user,login_required
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError

from apps.crud.models import User

dt = Blueprint("natyukatu",
                __name__,
                template_folder="templates",
                static_folder="static",)


# =====================================
# 共通処理
# =====================================

def make_id():
    """IDを生成する"""
    return uuid4().hex[:20]


def get_user_id():
    """ログインユーザーのIDを取得する"""
    return current_user.user_id


def get_recruitment(active_id):
    """募集情報を1件取得する"""
    recruitment = Recuruitment.query.filter_by(
        active_id=active_id
    ).first()

    if recruitment is None:
        abort(404)

    return recruitment


# =====================================
# ① 募集一覧取得・検索・絞り込み
# =====================================

@natyukatu.route("/")
def index():
    return render_template("natyukatu/top.html")


@natyukatu.route("/activities", methods=["GET", "POST"])
def activities():
    form = SearchForm()

    form.tag_id.choices = [
        ("", "すべて")
    ] + [
        (tag.tag_id, tag.tag_name)
        for tag in RecuruitmentTag.query.all()
    ]

    query = Recuruitment.query.filter_by(
        status="募集中",
        review_status="確認済み"
    )

    if form.validate_on_submit():
        keyword = form.keyword.data

        if keyword:
            query = query.filter(
                db.or_(
                    Recuruitment.title.contains(keyword),
                    Recuruitment.description.contains(keyword)
                )
            )

        if form.location_prefecture.data:
            query = query.filter_by(
                location_prefecture=form.location_prefecture.data
            )

        if form.location_city.data:
            query = query.filter_by(
                location_city=form.location_city.data
            )

        if form.tag_id.data:
            query = query.filter_by(
                tag_id=form.tag_id.data
            )

        if form.start_at.data:
            query = query.filter(
                Recuruitment.start_at >= form.start_at.data
            )

    recruitments = query.order_by(
        Recuruitment.created_at.desc()
    ).all()

    return render_template(
        "natyukatu/activities.html",
        form=form,
        recruitments=recruitments
    )


# =====================================
# ② 募集詳細・閲覧履歴
# =====================================

@natyukatu.route("/activities/<active_id>")
def activity_detail(active_id):
    recruitment = get_recruitment(active_id)

    if current_user.is_authenticated:
        history = ViewHistory(
            id=None,
            active_id=active_id,
            user_id=get_user_id(),
            apdate_at=datetime.now()
        )

        db.session.add(history)
        db.session.commit()

    return render_template(
        "natyukatu/activity_detail.html",
        recruitment=recruitment
    )


# =====================================
# ③ お気に入り登録
# =====================================

@natyukatu.route("/favorites/add/<active_id>", methods=["POST"])
@login_required
def add_favorite(active_id):
    recruitment = get_recruitment(active_id)

    favorite = Like.query.filter_by(
        user_id=get_user_id(),
        active_id=active_id
    ).first()

    if favorite is None:
        favorite = Like(
            favorite_id=make_id(),
            user_id=get_user_id(),
            active_id=recruitment.active_id
        )

        db.session.add(favorite)
        db.session.commit()

    flash("お気に入りに登録しました")

    return redirect(url_for(
        "natyukatu.activity_detail",
        active_id=active_id
    ))


# =====================================
# ④ お気に入り解除
# =====================================

@natyukatu.route("/favorites/delete/<favorite_id>", methods=["POST"])
@login_required
def delete_favorite(favorite_id):
    favorite = Like.query.filter_by(
        favorite_id=favorite_id,
        user_id=get_user_id()
    ).first_or_404()

    db.session.delete(favorite)
    db.session.commit()

    flash("お気に入りを解除しました")

    return redirect(url_for("natyukatu.favorites"))


# =====================================
# ⑤ お気に入り一覧取得
# =====================================

@natyukatu.route("/favorites")
@login_required
def favorites():
    favorites = Like.query.filter_by(
        user_id=get_user_id()
    ).all()

    return render_template(
        "natyukatu/favorites.html",
        favorites=favorites
    )


# =====================================
# ⑥ 閲覧履歴一覧取得
# =====================================

@natyukatu.route("/history/views")
@login_required
def view_histories():
    histories = ViewHistory.query.filter_by(
        user_id=get_user_id()
    ).order_by(
        ViewHistory.apdate_at.desc()
    ).all()

    return render_template(
        "natyukatu/view_histories.html",
        histories=histories
    )


# =====================================
# ⑦ 参加履歴・募集履歴取得
# =====================================

@natyukatu.route("/participations")
@login_required
def participations():
    histories = ParticipationHistory.query.filter_by(
        user_id=get_user_id()
    ).all()

    return render_template(
        "natyukatu/participations.html",
        histories=histories
    )


@natyukatu.route("/recruitments")
@login_required
def recruitments():
    histories = RecuruitmentHistory.query.filter_by(
        user_id=get_user_id()
    ).all()

    return render_template(
        "natyukatu/recruitments.html",
        histories=histories
    )


# =====================================
# ⑧ 新規募集登録
# =====================================

@natyukatu.route("/recruitments/new", methods=["GET", "POST"])
@login_required
def create_recruitment():
    form = RecruitmentForm()

    form.tag_id.choices = [
        (tag.tag_id, tag.tag_name)
        for tag in RecuruitmentTag.query.all()
    ]

    if form.validate_on_submit():
        recruitment = Recuruitment(
            active_id=make_id(),
            user_id=get_user_id(),
            title=form.title.data,
            description=form.description.data,
            photo=form.photo.data.read(),
            tag_id=form.tag_id.data,
            location_prefecture=form.location_prefecture.data,
            location_city=form.location_city.data,
            location_detail=form.location_detail.data,
            start_at=form.start_at.data,
            end_at=form.end_at.data,
            application_start_at=form.application_start_at.data,
            application_end_at=form.application_end_at.data,
            capacity=form.capacity.data,
            eligibility=form.eligibility.data,
            required_items=form.required_items.data,
            status="募集中",
            review_status="未確認"
        )

        db.session.add(recruitment)
        db.session.commit()

        flash("募集を登録しました")

        return redirect(url_for("natyukatu.recruitments"))

    return render_template(
        "natyukatu/create_recruitment.html",
        form=form
    )


# =====================================
# ⑨ 募集情報更新
# =====================================

@natyukatu.route(
    "/recruitments/<active_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_recruitment(active_id):
    recruitment = get_recruitment(active_id)

    if recruitment.user_id != get_user_id():
        abort(403)

    form = RecruitmentUpdateForm()

    form.tag_id.choices = [
        (tag.tag_id, tag.tag_name)
        for tag in RecuruitmentTag.query.all()
    ]

    if form.validate_on_submit():
        recruitment.title = form.title.data
        recruitment.description = form.description.data

        if form.photo.data:
            recruitment.photo = form.photo.data.read()

        recruitment.tag_id = form.tag_id.data
        recruitment.location_prefecture = form.location_prefecture.data
        recruitment.location_city = form.location_city.data
        recruitment.location_detail = form.location_detail.data
        recruitment.start_at = form.start_at.data
        recruitment.end_at = form.end_at.data
        recruitment.application_start_at = form.application_start_at.data
        recruitment.application_end_at = form.application_end_at.data
        recruitment.capacity = form.capacity.data
        recruitment.eligibility = form.eligibility.data
        recruitment.required_items = form.required_items.data

        db.session.commit()

        flash("募集情報を更新しました")

        return redirect(url_for("natyukatu.recruitments"))

    elif request.method == "GET":
        form.title.data = recruitment.title
        form.description.data = recruitment.description
        form.tag_id.data = recruitment.tag_id
        form.location_prefecture.data = recruitment.location_prefecture
        form.location_city.data = recruitment.location_city
        form.location_detail.data = recruitment.location_detail
        form.start_at.data = recruitment.start_at
        form.end_at.data = recruitment.end_at
        form.application_start_at.data = recruitment.application_start_at
        form.application_end_at.data = recruitment.application_end_at
        form.capacity.data = recruitment.capacity
        form.eligibility.data = recruitment.eligibility
        form.required_items.data = recruitment.required_items

    return render_template(
        "natyukatu/edit_recruitment.html",
        form=form,
        recruitment=recruitment
    )


# =====================================
# ⑩ 募集削除
# =====================================

@natyukatu.route(
    "/recruitments/<active_id>/delete",
    methods=["POST"]
)
@login_required
def delete_recruitment(active_id):
    recruitment = get_recruitment(active_id)

    if recruitment.user_id != get_user_id():
        abort(403)

    db.session.delete(recruitment)
    db.session.commit()

    flash("募集を削除しました")

    return redirect(url_for("natyukatu.recruitments"))


# =====================================
# ⑪ 参加申し込み
# =====================================

@natyukatu.route(
    "/activities/<active_id>/apply",
    methods=["GET", "POST"]
)
@login_required
def apply_activity(active_id):
    recruitment = get_recruitment(active_id)
    form = ParticipationForm()

    if form.validate_on_submit():

        if recruitment.application_end_at < datetime.now():
            flash("募集期間が終了しています")
            return redirect(url_for(
                "natyukatu.activity_detail",
                active_id=active_id
            ))

        entry = Entry(
            applicant_id=make_id(),
            activity_id=active_id,
            user_id=get_user_id(),
            particpant_count=form.participant_count.data,
            message=form.message.data,
            status="申込中",
            cansel_at=datetime.now()
        )

        db.session.add(entry)
        db.session.commit()

        flash("参加申し込みが完了しました")

        return redirect(url_for("natyukatu.apply_complete"))

    return render_template(
        "natyukatu/apply.html",
        form=form,
        recruitment=recruitment
    )


# =====================================
# ⑫ 申込完了画面
# =====================================

@natyukatu.route("/apply/complete")
@login_required
def apply_complete():
    return render_template("natyukatu/apply_complete.html")


# =====================================
# ⑬ 申込者一覧取得
# =====================================

@natyukatu.route(
    "/recruitments/<active_id>/applicants"
)
@login_required
def applicants(active_id):
    recruitment = get_recruitment(active_id)

    if recruitment.user_id != get_user_id():
        abort(403)

    entries = Entry.query.filter_by(
        activity_id=active_id
    ).all()

    return render_template(
        "natyukatu/applicants.html",
        entries=entries,
        recruitment=recruitment
    )


# =====================================
# ⑭ 申込状態変更（可・否）
# =====================================

@natyukatu.route(
    "/applicants/<applicant_id>/decision",
    methods=["POST"]
)
@login_required
def applicant_decision(applicant_id):
    entry = Entry.query.filter_by(
        applicant_id=applicant_id
    ).first_or_404()

    recruitment = get_recruitment(entry.activity_id)

    if recruitment.user_id != get_user_id():
        abort(403)

    form = ApplicantDecisionForm()

    if form.validate_on_submit():
        entry.status = form.status.data
        entry.update_at = datetime.now()

        db.session.commit()

        flash("申込状態を変更しました")

    return redirect(url_for(
        "natyukatu.applicants",
        active_id=entry.activity_id
    ))


# =====================================
# ⑮ 申込者を一覧から削除
# =====================================

@natyukatu.route(
    "/applicants/<applicant_id>/delete",
    methods=["POST"]
)
@login_required
def delete_applicant(applicant_id):
    entry = Entry.query.filter_by(
        applicant_id=applicant_id
    ).first_or_404()

    recruitment = get_recruitment(entry.activity_id)

    if recruitment.user_id != get_user_id():
        abort(403)

    db.session.delete(entry)
    db.session.commit()

    flash("申込者を削除しました")

    return redirect(url_for(
        "natyukatu.applicants",
        active_id=recruitment.active_id
    ))


# =====================================
# ⑯ 活動用メッセージ投稿
# =====================================

@natyukatu.route(
    "/messages/<active_id>",
    methods=["GET", "POST"]
)
@login_required
def messages(active_id):
    recruitment = get_recruitment(active_id)
    form = MessageForm()

    if form.validate_on_submit():
        message = ActiveMessagae(
            user_id=get_user_id(),
            message=form.message.data,
            nickname=current_user.nickname,
            created_at=datetime.now(),
            post_at=datetime.now(),
            update_at=datetime.now()
        )

        db.session.add(message)
        db.session.commit()

        flash("メッセージを投稿しました")

        return redirect(url_for(
            "natyukatu.messages",
            active_id=active_id
        ))

    return render_template(
        "natyukatu/messages.html",
        form=form,
        recruitment=recruitment
    )


# =====================================
# ⑰ お問い合わせ
# =====================================

@natyukatu.route(
    "/contact",
    methods=["GET", "POST"]
)
@login_required
def contact():
    form = ContactForm()

    if form.validate_on_submit():
        contact_history = ContactHistory(
            contact_id=make_id(),
            user_id=get_user_id(),
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            body=form.body.data
        )

        db.session.add(contact_history)
        db.session.commit()

        flash("お問い合わせを送信しました")

        return redirect(url_for("natyukatu.index"))

    return render_template(
        "natyukatu/contact.html",
        form=form
    )


# =====================================
# ⑱ サンクスボタン
# =====================================

@natyukatu.route(
    "/thanks/<active_id>/<user_id>",
    methods=["POST"]
)
@login_required
def thanks(active_id, user_id):
    recruitment = get_recruitment(active_id)

    if recruitment.user_id != get_user_id():
        abort(403)

    point = ThanksPoint(
        point_id=make_id(),
        user_id=user_id,
        activity_id=active_id,
        record_id=make_id(),
        point_count=1
    )

    db.session.add(point)
    db.session.commit()

    flash("サンクスポイントを送りました")

    return redirect(url_for(
        "natyukatu.participations"
    ))


# =====================================
# ⑲ ランキング生成
# =====================================

@natyukatu.route("/ranking")
def ranking():
    results = db.session.query(
        ThanksPoint.user_id,
        db.func.sum(ThanksPoint.point_count).label("total_points")
    ).group_by(
        ThanksPoint.user_id
    ).order_by(
        db.func.sum(ThanksPoint.point_count).desc()
    ).all()

    return render_template(
        "natyukatu/ranking.html",
        rankings=results
    )


# =====================================
# ⑳ ユーザー情報変更
# =====================================

@natyukatu.route(
    "/mypage/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_profile():
    form = UserUpdateForm()

    user = User.query.filter_by(
        user_id=get_user_id()
    ).first_or_404()

    if form.validate_on_submit():
        user.username = form.username.data
        user.nickname = form.nickname.data
        user.age = form.age.data
        user.email = form.email.data
        user.emergency_contact = form.emergency_contact.data

        db.session.commit()

        flash("ユーザー情報を変更しました")

        return redirect(url_for("natyukatu.mypage"))

    elif request.method == "GET":
        form.username.data = user.username
        form.nickname.data = user.nickname
        form.age.data = user.age
        form.email.data = user.email
        form.emergency_contact.data = user.emergency_contact

    return render_template(
        "natyukatu/edit_profile.html",
        form=form
    )


# =====================================
# ㉑ ユーザー退会
# =====================================

@natyukatu.route(
    "/mypage/withdrawal",
    methods=["GET", "POST"]
)
@login_required
def withdrawal():
    form = WithdrawalForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            user_id=get_user_id()
        ).first_or_404()

        if not user.check_password(form.password.data):
            flash("パスワードが違います")
            return render_template(
                "natyukatu/withdrawal.html",
                form=form
            )

        db.session.delete(user)
        db.session.commit()

        from flask_login import logout_user
        logout_user()

        flash("退会しました")

        return redirect(url_for("natyukatu.index"))

    return render_template(
        "natyukatu/withdrawal.html",
        form=form
    )


# =====================================
# ㉒ 管理者用削除
# =====================================

@natyukatu.route(
    "/admin/recruitments/<active_id>/delete",
    methods=["POST"]
)
@login_required
def admin_delete_recruitment(active_id):
    # 管理者権限の確認をここに追加する
    recruitment = get_recruitment(active_id)

    db.session.delete(recruitment)
    db.session.commit()

    flash("募集を削除しました")

    return redirect(url_for("natyukatu.admin"))


@natyukatu.route("/admin")
@login_required
def admin():
    recruitments = Recuruitment.query.all()
    entries = Entry.query.all()
    users = User.query.all()

    return render_template(
        "natyukatu/admin.html",
        recruitments=recruitments,
        entries=entries,
        users=users
    )
