from datetime import datetime
import os
import numpy as np
from pathlib import Path
from apps.app import db
from apps.crud.models import User
from flask import Blueprint,render_template,current_app,send_from_directory
import pandas as pd
import joblib
from sqlalchemy import desc
from sklearn.feature_extraction.text import CountVectorizer
from apps.natyukatu.data_init import init_data,delete
 
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
    Recruitment,
    Like,
    ViewHistory,
    RecruitmentTag,
    Tag,
    ActiveMessage,
    ThanksPoint,
    ContactHistory,
    ParticipationHistory,
    RecruitmentHistory,
    Status
)
 
from apps.natyukatu.forms import (
    ParticipationForm,
    RecruitmentForm,
    ContactForm,
    LikeForm,
    MessageForm,
    RecruitmentDeleteForm,
    HistoryUpdateForm,
    SearchForm,
    ApplicantDecisionForm,
    WithdrawalForm,
)

from apps.crud.forms import UserForm
 
from flask_login import current_user,login_required
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError
 
from apps.crud.models import User
 
dt = Blueprint("natyukatu",
                __name__,
                template_folder="templates",
                static_folder="static",)
 
#ユーザーIDを取得
def get_user_id():
    if current_user.is_authenticated:
        # Userモデルの属性名に合わせて user_id または id を取得
        return getattr(current_user, 'user_id', getattr(current_user, 'id', None))
    return None
 
#募集情報を取得
def get_recruitment(recruitment_id):
    recruitment = Recruitment.query.filter_by(
        id=recruitment_id
    ).first()
 
    if recruitment is None:
        abort(404)
 
    return recruitment

#トップ画面
@dt.route("/", methods=["GET", "POST"])
def top():
 
    # 各メソッドを持ってくる
    # ユーザーID取得
    user_id = get_user_id()
 
    # データベース初期登録
    #delete()
    #init_data()
    
    # 検索フォーム
    search_form = SearchForm(prefix="search")
 
    # タグ検索用
    set_tag_choices(search_form)
 
    # タグを分類ごとに取得
    tag_groups = {
        # 1：産業種別
        1: RecruitmentTag.query.filter_by(tag_kinds=1).all(),
 
        # 2：作業内容・参加条件・その他
        2: RecruitmentTag.query.filter_by(tag_kinds=2).all(),
 
        # 3：都道府県
        3: RecruitmentTag.query.filter_by(tag_kinds=3).all(),
 
        # 4：市区町村
        4: RecruitmentTag.query.filter_by(tag_kinds=4).all(),
    }
 
    # お気に入りフォーム
    like_form = LikeForm(prefix="like")
 
    # POSTリクエスト時の処理
    if request.method == "POST":
 
        # お気に入りボタンが押された場合
        if "like-submit" in request.form and like_form.validate_on_submit():
            recruitment_id = int(like_form.recruitment_id.data)
 
            existing_like = Like.query.filter_by(
                user_id=user_id,
                recruitment_id=recruitment_id
            ).first()
 
            if existing_like:
                delete_like(user_id, recruitment_id)
            else:
                add_like(user_id, recruitment_id)
 
            return redirect(url_for("natyukatu.top"))
 
    # 入力されたタグIDを取得
    selected_tag_ids = search_form.tag_id.data or []
 
    # 入力された検索ワード取得
    keyword = search_form.keyword.data if hasattr(search_form, 'keyword') else None
 
    # 絞り込み条件を反映した募集一覧を取得
    recruitments = get_recruitment_list(
        keyword=keyword,
        tag_ids=selected_tag_ids
    )
 
    # お気に入り一覧取得
    like_list = get_like_list(user_id)
 
    # 閲覧履歴取得
    view_history_list = get_view_history_list(user_id)
 
    return render_template(
        "natyukatu/top.html",
        form=search_form,
        like_form=like_form,
        recruitments=recruitments,
        like_list=like_list,
        view_history_list=view_history_list,
        tag_groups=tag_groups,
    )
 
# 募集一覧取得（タグとワードで絞り込み有）
def get_recruitment_list(keyword=None, tag_ids=None):
    query = db.session.query(Recruitment).outerjoin(
        Tag,
        Recruitment.id == Tag.recruitment_id
    )
    
    # キーワード検索がある場合
    if keyword:
        query = query.filter(Recruitment.title.like(f"%{keyword}%"))
        
    # タグIDをリスト形式に統一
    if tag_ids is None:
        tag_ids = []
    elif isinstance(tag_ids, (int, str)):
        tag_ids = [int(tag_ids)] if str(tag_ids).isdigit() else []
    else:
        tag_ids = [int(tag_id) for tag_id in tag_ids if str(tag_id).isdigit()]
           
        recruitments = query.distinct().order_by(desc(Recruitment.created_at)).all()
        return recruitments

#タグ取得
def set_tag_choices(form):
    form.tag_id.choices = [(0, "すべて")] + [
        (tag.id, tag.tag_name) 
        for tag in RecruitmentTag.query.all()
    ]

# お気に入り一覧取得
def get_like_list(user_id):
    query = (
        db.session.query(Recruitment)
        .join(Like, Recruitment.id == Like.recruitment_id)  # Likeテーブルと結合
        .filter(Like.user_id == user_id)  # ログイン中のユーザーIDで絞り込み
        .order_by(desc(Recruitment.created_at))
    )
    recruitments = query.all()
    return recruitments
 
#閲覧履歴一覧取得
def get_view_history_list(user_id):
    query = (
        db.session.query(Recruitment)
        .join(ViewHistory, Recruitment.id == ViewHistory.recruitment_id)  
        .filter(ViewHistory.user_id == user_id)  # ログイン中のユーザーIDで絞り込み
        .order_by(desc(Recruitment.updated_at))
    )
    recruitments = query.all()
    return recruitments

#お気に入り登録
def add_like(user_id,recruitment_id):
    recruitment = get_recruitment(recruitment_id)
 
    like = Like.query.filter_by(
        user_id=user_id,
        recruitment_id=recruitment_id
    ).first()
 
    if like is None:
        like = Like(
            user_id=user_id,
            recruitment_id=recruitment_id
        )
        db.session.add(like)
        db.session.commit()
 
#お気に入り解除
def delete_like(user_id,recruitment_id):

    like = Like.query.filter_by(
        user_id=user_id,
        recruitment_id=recruitment_id
    ).first()

    #データが存在していれば削除してコミット
    if like is not None:
        db.session.delete(like)
        db.session.commit()

# 新規募集登録
@dt.route("/recruitment_register", methods=["GET", "POST"])
@login_required
def recruitment_register():
    form = RecruitmentForm()

    # 都道府県(tag_kinds=3)の choices をセット
    prefecture_tags = RecruitmentTag.query.filter_by(tag_kinds=3).all()
    form.location_prefecture.choices = [("", "選択してください")] + [
        (tag.tag_name, tag.tag_name)
        for tag in prefecture_tags
    ]

    # 市町村(tag_kinds=4)の choices をセット（必須）
    city_tags = RecruitmentTag.query.filter_by(tag_kinds=4).all()
    form.location_city.choices = [("", "選択してください")] + [
        (tag.tag_name, tag.tag_name)
        for tag in city_tags
    ]

    # GET時の初期値を岩手県にする場合
    if request.method == "GET" and not form.location_prefecture.data:
        form.location_prefecture.data = "岩手県"

    if form.validate_on_submit():
        selected_pref = form.location_prefecture.data or "岩手県"
        selected_city = form.location_city.data

        recruitment = Recruitment(
            user_id=get_user_id(),
            title=form.title.data,
            description=form.description.data,
            photo=form.photo.data.read(),
            location_prefecture=selected_pref,  # ← ここ
            location_city=selected_city,
            location_detail=form.location_detail.data,
            start_at=form.start_at.data,
            end_at=form.end_at.data,
            application_start_at=form.application_start_at.data,
            application_end_at=form.application_end_at.data,
            capacity=form.capacity.data,
            eligibility=form.eligibility.data,
            required_items=form.required_items.data,
            status="",
        )

        db.session.add(recruitment)
        db.session.flush()

        # 種類（農業、漁業、林業）
        selected_kind = form.kind.data
        selected_kind_id = RecruitmentTag.query.filter_by(tag_name=selected_kind, tag_kinds=1).first()
        if selected_kind_id:
            search_tag = Tag(
                tag_id=selected_kind_id.id,
                recruitment_id=recruitment.id
            )
            db.session.add(search_tag)

        # 県（岩手県固定で紐付け）
        pref_tag = RecruitmentTag.query.filter_by(tag_name="岩手県", tag_kinds=3).first()
        if pref_tag:
            db.session.add(Tag(tag_id=pref_tag.id, recruitment_id=recruitment.id))

        # 市
        city_tag = RecruitmentTag.query.filter_by(tag_name=selected_city, tag_kinds=4).first()
        if city_tag:
            db.session.add(Tag(tag_id=city_tag.id, recruitment_id=recruitment.id))

        # スペース区切りで分割
        tags = form.tag.data.strip().split()
        for tag in tags:
            tag_obj = RecruitmentTag.query.filter_by(tag_name=tag).first()
            if not tag_obj:
                tag_obj = RecruitmentTag(tag_name=tag, tag_kinds=2)
                db.session.add(tag_obj)
                db.session.flush()

            search_tag = Tag(
                tag_id=tag_obj.id,
                recruitment_id=recruitment.id
            )
            db.session.add(search_tag)

        recruitment_history = RecruitmentHistory(
            recruitment_id=recruitment.id,
            user_id=get_user_id(),
            status_id=3,
        )
        db.session.add(recruitment_history)
        db.session.commit()

        flash("募集を登録しました")
        return redirect(url_for("natyukatu.recruitment_register_complete"))

    return render_template(
        "natyukatu/recruitment_register.html",
        form=form
    )

#新規募集登録完了画面
@dt.route('/recruitment_register_complete')
@login_required
def recruitment_register_complete():
    return render_template('natyukatu/recruitment_register_complete.html')

#ユーザー詳細画面
@dt.route("/user_detail")
@login_required
def userDetail():
    return render_template("natyukatu/user_detail.html")

#ユーザー情報変更 
@dt.route(
    "/mypage/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_profile():
    form = UserForm()
 
    user = User.query.filter_by(
        id=get_user_id()
    ).first_or_404()
 
    if form.validate_on_submit():
        user.username = form.username.data
        user.nickname = form.nickname.data
        user.age = form.age.data
        user.email = form.email.data
        user.phone_number = form.phone_number.data
 
        db.session.commit()
 
        flash("ユーザー情報を変更しました")
 
        return redirect(url_for("natyukatu.user_detail_update_complete"))
 
    elif request.method == "GET":
        form.username.data = user.username
        form.nickname.data = user.nickname
        form.age.data = user.age
        form.email.data = user.email
        form.phone_number.data = user.phone_number
 
    return render_template(
        "natyukatu/user_detail_update.html",
        form=form
    )

#ユーザー情報変更完了画面
@dt.route('/user_detail_update_complete')
@login_required
def user_detail_update_complete():
    return render_template('natyukatu/user_detail_update_complete.html')

#退会
@dt.route("/mypage/withdrawal", methods=["GET", "POST"])
@login_required
def withdrawal():
    form = WithdrawalForm()
 
    if form.validate_on_submit():
        user = User.query.filter_by(
            id=get_user_id()
        ).first_or_404()
 
        # パスワードがハッシュ化されている場合のチェック
        if not user.verify_password(form.password.data):
            flash("パスワードが違います")
            return render_template(
                "natyukatu/withdrawal.html",
                form=form
            )
 
        # ユーザーデータを削除してログアウト
        db.session.delete(user)
        db.session.commit()
 
        from flask_login import logout_user
        logout_user()
 
        flash("退会しました")
 
        # 退会完了画面へリダイレクト（※ルート名が withdrawal_complete の場合）
        return redirect(url_for("natyukatu.withdrawal_complete"))
 
    return render_template(
        "natyukatu/withdrawal.html",
        form=form
    )

#退会完了
@dt.route("/mypage/withdrawal-complete")
@login_required
def withdrawal_complete():
    return render_template("natyukatu/withdrawal_complete.html")

#お問い合わせ 
@dt.route(
    "/contact",
    methods=["GET", "POST"]
)
@login_required
def contact():
    form = ContactForm()
 
    if form.validate_on_submit():
        contact_history = ContactHistory(
            id=get_user_id(),
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            body=form.body.data
        )
 
        db.session.add(contact_history)
        db.session.commit()
 
        flash("お問い合わせを送信しました")
 
        return redirect(url_for("natyukatu.top"))
 
    return render_template(
        "natyukatu/contact.html",
        form=form
    )
 

#募集詳細
@dt.route("/recruitment_detail/<recruitment_id>")
def recruitment_detail(recruitment_id):
    recruitment = get_recruitment(recruitment_id)
 
    if current_user.is_authenticated:
        history = ViewHistory(
            recruitment_id=recruitment_id,
            user_id=get_user_id(),
            added_at=datetime.now()
        )


        db.session.add(history)
        db.session.commit()
 
    return render_template(
        "natyukatu/recruitment_detail.html",
        recruitment=recruitment,
    )
 
#参加申し込み
@dt.route(
    "/participation_application/<recruitment_id>/apply",
    methods=["GET", "POST"]
)
@login_required
def participation_application(recruitment_id):
    recruitment = get_recruitment(recruitment_id)
    form = ParticipationForm()
    user_id = get_user_id()

    #すでに同じユーザーがこの募集に申し込んでいるかチェック
    existing_entry = ParticipationHistory.query.filter_by(
        recruitment_id=recruitment_id,
        user_id=user_id
    ).first()

    if existing_entry:
        return redirect(url_for(
            "natyukatu.participation_application_already",
            recruitment_id=recruitment_id
        ))
    
    if form.validate_on_submit():
        if recruitment.application_end_at < datetime.now():
            flash("募集期間が終了しています")
            return redirect(url_for(
                "natyukatu.recruitment_detail",
                recruitment_id=recruitment_id
            ))
 
        entry = ParticipationHistory(
            recruitment_id=recruitment_id,
            user_id=get_user_id(),
            message=form.message.data,
            status_id=3,
        )
 
        db.session.add(entry)
        db.session.commit()
 
        flash("参加申し込みが完了しました")
 
        return redirect(url_for("natyukatu.participation_application_complete"))
 
    return render_template(
        "natyukatu/participation_application.html",
        form=form,
        recruitment=recruitment
    )
 
#申込完了画面
@dt.route("/participation_application_complete")
@login_required
def participation_application_complete():
    return render_template("natyukatu/participation_application_complete.html")

#申込済み画面
@dt.route("/natyukatu.participation_application_already/<recruitment_id>",methods=["GET"])
@login_required
def participation_application_already(recruitment_id):
    recruitment = get_recruitment(recruitment_id)
    return render_template(
        "natyukatu/participation_application_already.html",
        recruitment=recruitment
        )
 
#参加履歴 
@dt.route("/participation_history" ,methods=["GET", "POST"])
@login_required
def participation_history():
    participation_histories = ParticipationHistory.query.filter_by(
        user_id=get_user_id()
    ).all()
    
    return render_template(
        "natyukatu/participation_history.html",
        participation_histories=participation_histories
    )
 
#募集履歴
@dt.route("/recruitment_history")
@login_required
def recruitment_history():
    histories = RecruitmentHistory.query.filter_by(
        user_id=get_user_id()
    ).all()
 
    return render_template(
        "natyukatu/recruitment_history.html",
        histories=histories
    )

#募集情報更新
@dt.route(
    "/recruitment_update/<recruitment_id>",
    methods=["GET", "POST"]
)
@login_required
def recruitment_update(recruitment_id):
    recruitment = get_recruitment(recruitment_id)

    if recruitment.user_id != get_user_id():
        abort(403)

    form = RecruitmentForm()

    # 都道府県(tag_kinds=3)の choices をセット
    prefecture_tags = RecruitmentTag.query.filter_by(tag_kinds=3).all()
    form.location_prefecture.choices = [("", "選択してください")] + [
        (tag.tag_name, tag.tag_name)
        for tag in prefecture_tags
    ]

    # 市町村(tag_kinds=4)の choices をセット
    city_tags = RecruitmentTag.query.filter_by(tag_kinds=4).all()
    form.location_city.choices = [("", "選択してください")] + [
        (tag.tag_name, tag.tag_name)
        for tag in city_tags
    ]

    if form.validate_on_submit():
        selected_pref = form.location_prefecture.data or "岩手県"
        selected_city = form.location_city.data

        recruitment.title = form.title.data
        recruitment.description = form.description.data

        if form.photo.data:
            recruitment.photo = form.photo.data.read()

        recruitment.location_prefecture = selected_pref
        recruitment.location_city = selected_city
        recruitment.location_detail = form.location_detail.data
        recruitment.start_at = form.start_at.data
        recruitment.end_at = form.end_at.data
        recruitment.application_start_at = form.application_start_at.data
        recruitment.application_end_at = form.application_end_at.data
        recruitment.capacity = form.capacity.data
        recruitment.eligibility = form.eligibility.data
        recruitment.required_items = form.required_items.data

        # 一旦、この募集に紐づく Tag レコードを削除して再登録
        Tag.query.filter_by(recruitment_id=recruitment.id).delete()

        # 1. 種類（農業、漁業、林業）のタグを登録
        selected_kind = form.kind.data.lstrip("#") if form.kind.data else ""
        if selected_kind:
            selected_kind_obj = RecruitmentTag.query.filter_by(
                tag_name=selected_kind,
                tag_kinds=1
            ).first()
            if selected_kind_obj:
                db.session.add(Tag(
                    tag_id=selected_kind_obj.id,
                    recruitment_id=recruitment.id
                ))

        # 2. 県（tag_kinds=3）のタグを登録
        pref_tag = RecruitmentTag.query.filter_by(
            tag_name=selected_pref,
            tag_kinds=3
        ).first()
        if pref_tag:
            db.session.add(Tag(
                tag_id=pref_tag.id,
                recruitment_id=recruitment.id
            ))

        # 3. 市町村（tag_kinds=4）のタグを登録
        city_tag = RecruitmentTag.query.filter_by(
            tag_name=selected_city,
            tag_kinds=4
        ).first()
        if city_tag:
            db.session.add(Tag(
                tag_id=city_tag.id,
                recruitment_id=recruitment.id
            ))

        # 4. 自由入力タグ（tag_kinds=2）をスペース区切りで分割して登録
        raw_tags = set(form.tag.data.replace(" ", " ").strip().split()) if form.tag.data else set()
        for raw_tag in raw_tags:
            tag_name = raw_tag.lstrip("#").strip()
            if not tag_name:
                continue

            tag_obj = RecruitmentTag.query.filter_by(tag_name=tag_name).first()
            if not tag_obj:
                tag_obj = RecruitmentTag(tag_name=tag_name, tag_kinds=2)
                db.session.add(tag_obj)
                db.session.flush()

            db.session.add(Tag(
                tag_id=tag_obj.id,
                recruitment_id=recruitment.id
            ))

        db.session.commit()

        flash("募集情報を更新しました")
        return redirect(url_for("natyukatu.recruitment_history"))

    elif request.method == "GET":
        form.title.data = recruitment.title
        form.description.data = recruitment.description
        form.location_prefecture.data = recruitment.location_prefecture or "岩手県"
        form.location_city.data = recruitment.location_city
        form.location_detail.data = recruitment.location_detail
        form.start_at.data = recruitment.start_at
        form.end_at.data = recruitment.end_at
        form.application_start_at.data = recruitment.application_start_at
        form.application_end_at.data = recruitment.application_end_at
        form.capacity.data = recruitment.capacity
        form.eligibility.data = recruitment.eligibility
        form.required_items.data = recruitment.required_items

        associated_tags = (
            RecruitmentTag.query
            .join(Tag)
            .filter(Tag.recruitment_id == recruitment.id)
            .all()
        )

        kind_tag = next((t for t in associated_tags if t.tag_kinds == 1), None)
        if kind_tag:
            # RecruitmentForm の kind の choices が "#農業" 形式なら "#" を付ける
            form.kind.data = f"#{kind_tag.tag_name}"

        free_tags = [t.tag_name for t in associated_tags if t.tag_kinds == 2]
        form.tag.data = " ".join(free_tags)

    return render_template(
        "natyukatu/recruitment_update.html",
        form=form,
        recruitment=recruitment
    )


#募集更新完了画面
@dt.route("/recruitment_update_complete")
@login_required
def recruitment_update_complete():
    return render_template("natyukatu/recruitment_update_complete.html")
 
#募集削除
@dt.route(
    "/recruitment_delete/<recruitment_id>",
    methods=["POST"]
)
@login_required
def recruitment_delete(recruitment_id):
    recruitment = get_recruitment(recruitment_id)
 
    if recruitment.user_id != get_user_id():
        abort(403)
 
    db.session.delete(recruitment)
    db.session.commit()
 
    return redirect(url_for("natyukatu.recruitment_delete_complete"))

#募集削除完了画面
@dt.route("/recruitment_delete_complete")
@login_required
def recruitment_delete_complete():
    return render_template("natyukatu/recruitment_delete_complete.html")


#活動用画面
@dt.route(
    "/for_active/<recruitment_id>",
    methods=["GET", "POST"])
@login_required
def for_active(recruitment_id):

    #募集情報を取得
    recruitment = get_recruitment(recruitment_id)

    #メッセージ投稿フォーム
    form = MessageForm()

    return render_template(
        "natyukatu/for_active.html",
        recruitment=recruitment,
        form=form
    )
# =====================================
# ⑬ 申込者一覧取得
# =====================================
 
@dt.route(
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
 
@dt.route(
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
 
@dt.route(
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
 
@dt.route(
    "/messages/<active_id>",
    methods=["GET", "POST"]
)
@login_required
def messages(active_id):
    recruitment = get_recruitment(active_id)
    form = MessageForm()
 
    if form.validate_on_submit():
        message = ActiveMessage(
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
# ⑱ サンクスボタン
# =====================================
 
@dt.route(
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
 
@dt.route("/ranking")
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
# ㉒ 管理者用削除
# =====================================
 
@dt.route(
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
 
 
@dt.route("/admin")
@login_required
def admin():
    recruitments = Recruitment.query.all()
    entries = Entry.query.all()
    users = User.query.all()
 
    return render_template(
        "natyukatu/admin.html",
        recruitments=recruitments,
        entries=entries,
        users=users
    )
 
