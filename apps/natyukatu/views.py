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
import io
from flask import send_file
from sqlalchemy.exc import SQLAlchemyError
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
    ContactHistory,
    ParticipationHistory,
    RecruitmentHistory,
    Status,
    RecruitmentImage,
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
    UserUpdateForm,
    RecruitmentUpdateForm,
    ParticipationQuitForm,
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

# 募集画像を表示
@dt.route("/recruitment/<int:recruitment_id>/photo")
def recruitment_photo(recruitment_id):

    recruitment = get_recruitment(recruitment_id)

    if not recruitment.photo:
        abort(404)

    return send_file(
        io.BytesIO(recruitment.photo),
        mimetype=recruitment.photo_mimetype or "image/jpeg"
    )


# 2枚目以降の募集画像を表示
@dt.route("/recruitment_image/<int:image_id>")
def recruitment_extra_photo(image_id):
    image = RecruitmentImage.query.get_or_404(image_id)

    if not image.image_data:
        abort(404)

    return send_file(
        io.BytesIO(image.image_data),
        mimetype=image.mimetype or "image/jpeg"
    )


# 募集動画を表示
@dt.route("/recruitment/<int:recruitment_id>/video")
def recruitment_video(recruitment_id):

    recruitment = get_recruitment(recruitment_id)

    if not recruitment.video:
        abort(404)

    return send_file(
        io.BytesIO(recruitment.video),
        mimetype=recruitment.video_mimetype or "video/mp4"
    )

#トップ画面
@dt.route("/", methods=["GET", "POST"])
def top():

    # データベース初期登録
    #delete()
    #init_data()

    user_id = get_user_id()
    search_form = SearchForm(prefix="search")
    set_tag_choices(search_form)

    tag_groups = {
        1: RecruitmentTag.query.filter_by(tag_kinds=1).order_by(RecruitmentTag.tag_name).all(),
        2: RecruitmentTag.query.filter_by(tag_kinds=2).order_by(RecruitmentTag.tag_name).all(),
        3: RecruitmentTag.query.filter_by(tag_kinds=3).order_by(RecruitmentTag.tag_name).all(),
        4: RecruitmentTag.query.filter_by(tag_kinds=4).order_by(RecruitmentTag.tag_name).all(),
    }

    like_form = LikeForm(prefix="like")

    if request.method == "POST":
        if "like-submit" in request.form and like_form.validate_on_submit():
            if not current_user.is_authenticated:
                abort(403)
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

    # タグリンクからGETで来た場合も、通常の検索フォームと同じ条件で検索する
    if request.method == "GET" and request.args.get("tag_id"):
        try:
            selected_tag_ids = [int(value) for value in request.args.getlist("tag_id")]
        except (TypeError, ValueError):
            selected_tag_ids = []
        search_form.tag_id.data = selected_tag_ids
    else:
        selected_tag_ids = search_form.tag_id.data or []

    keyword = (search_form.keyword.data or request.args.get("keyword", "")).strip()
    sort_order = request.form.get("sort_order") or request.args.get("sort_order", "newest")
    allowed_sorts = {
        "newest", "oldest", "start_asc", "start_desc",
        "title_asc", "title_desc", "capacity_asc", "capacity_desc"
    }
    if sort_order not in allowed_sorts:
        sort_order = "newest"

    recruitments = get_recruitment_list(
        keyword=keyword,
        tag_ids=selected_tag_ids,
        sort_order=sort_order
    )
    like_list = get_like_list(user_id) if user_id else []
    view_history_list = get_view_history_list(user_id) if user_id else []
    recruitment_tags = get_recruitment_tag_map([item.id for item in recruitments])

    return render_template(
        "natyukatu/top.html",
        form=search_form,
        like_form=like_form,
        recruitments=recruitments,
        like_list=like_list,
        view_history_list=view_history_list,
        tag_groups=tag_groups,
        sort_order=sort_order,
        recruitment_tags=recruitment_tags,
    )


# 募集一覧取得（キーワード・タグ・並び順で絞り込み）
def get_recruitment_list(keyword=None, tag_ids=None, sort_order="newest"):
    query = Recruitment.query

    if keyword:
        query = query.filter(
            db.or_(
                Recruitment.title.ilike(f"%{keyword}%"),
                Recruitment.description.ilike(f"%{keyword}%"),
                Recruitment.location_prefecture.ilike(f"%{keyword}%"),
                Recruitment.location_city.ilike(f"%{keyword}%")
            )
        )

    normalized_ids = []
    for tag_id in (tag_ids or []):
        try:
            value = int(tag_id)
            if value > 0 and value not in normalized_ids:
                normalized_ids.append(value)
        except (TypeError, ValueError):
            continue

    if normalized_ids:
        query = query.join(Tag, Recruitment.id == Tag.recruitment_id).filter(
            Tag.tag_id.in_(normalized_ids)
        )

    sort_columns = {
        "newest": Recruitment.created_at.desc(),
        "oldest": Recruitment.created_at.asc(),
        "start_asc": Recruitment.start_at.asc(),
        "start_desc": Recruitment.start_at.desc(),
        "title_asc": Recruitment.title.asc(),
        "title_desc": Recruitment.title.desc(),
        "capacity_asc": Recruitment.capacity.asc(),
        "capacity_desc": Recruitment.capacity.desc(),
    }
    return query.distinct().order_by(
        sort_columns.get(sort_order, Recruitment.created_at.desc()),
        Recruitment.id.desc()
    ).all()

# 募集ごとのタグを取得（トップ一覧・募集詳細で共通利用）
def get_recruitment_tag_map(recruitment_ids):
    if not recruitment_ids:
        return {}

    rows = (
        db.session.query(Tag.recruitment_id, RecruitmentTag)
        .join(RecruitmentTag, Tag.tag_id == RecruitmentTag.id)
        .filter(Tag.recruitment_id.in_(recruitment_ids))
        .order_by(RecruitmentTag.tag_kinds, RecruitmentTag.tag_name)
        .all()
    )

    tag_map = {}
    for recruitment_id, tag in rows:
        tag_map.setdefault(recruitment_id, []).append(tag)

    return tag_map


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


        # 選択された画像を取得
        photos = [
            photo for photo in (form.photo.data or [])
            if photo and getattr(photo, "filename", "")
        ]

        # 画像形式を確認
        allowed_extensions = {"jpg", "jpeg", "png"}

        for photo in photos:
            extension = photo.filename.rsplit(".", 1)[-1].lower()

            if extension not in allowed_extensions:
                flash("画像はjpg、jpeg、png形式で選択してください")
                return render_template(
                    "natyukatu/recruitment_register.html",
                    form=form
                )

        # 最低1枚必要
        if not photos:
            flash("募集画像を1枚以上選択してください")
            return render_template(
                "natyukatu/recruitment_register.html",
                form=form
            )
        recruitment = Recruitment(
            user_id=get_user_id(),
            title=form.title.data,
            description=form.description.data,

            # 1枚目をメイン画像として保存
            photo=photos[0].read(),
            photo_mimetype=photos[0].mimetype,

            # 動画保存
            video=(
                form.video.data.read()
                if form.video.data and form.video.data.filename
                else None
            ),

            video_mimetype=(
                form.video.data.mimetype
                if form.video.data and form.video.data.filename
                else None
            ),

            # 以下は現在の設定をそのまま残す
            location_prefecture=selected_pref,
            location_city=selected_city,
            location_detail=form.location_detail.data,
            start_at=form.start_at.data,
            end_at=form.end_at.data,
            application_start_at=form.application_start_at.data,
            application_end_at=form.application_end_at.data,
            capacity=form.capacity.data,
            eligibility=form.eligibility.data,
            required_items=form.required_items.data,
            status=1,
        )

        db.session.add(recruitment)
        db.session.flush()

        # 2枚目以降を追加画像テーブルに保存
        # form.photo.data は MultipleFileField のため、選択画像のリストを使う
        for index, photo in enumerate(photos[1:], start=1):
            image = RecruitmentImage(
                recruitment_id=recruitment.id,
                image_data=photo.read(),
                mimetype=photo.mimetype or "image/jpeg",
                display_order=index
            )
            db.session.add(image)

        # 種類（農業、漁業、林業）
        selected_kind = form.kind.data.lstrip("#") if form.kind.data else ""
        selected_kind_id = RecruitmentTag.query.filter_by(tag_name=selected_kind, tag_kinds=1).first()
        if selected_kind_id:
            search_tag = Tag(
                tag_id=selected_kind_id.id,
                recruitment_id=recruitment.id
            )
            db.session.add(search_tag)

        # 県（岩手県固定で紐付け）
        pref_tag = RecruitmentTag.query.filter_by(tag_name=selected_pref, tag_kinds=3).first()
        if pref_tag:
            db.session.add(Tag(tag_id=pref_tag.id, recruitment_id=recruitment.id))

        # 市
        city_tag = RecruitmentTag.query.filter_by(tag_name=selected_city, tag_kinds=4).first()
        if city_tag:
            db.session.add(Tag(tag_id=city_tag.id, recruitment_id=recruitment.id))

        # スペース区切りで分割
        tags = (form.tag.data or "").strip().split()
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
    form = UserUpdateForm()
 
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
def withdrawal_complete():
    return render_template("natyukatu/withdrawal_complete.html")

#お問い合わせ 
@dt.route(
    "/contact",
    methods=["GET", "POST"]
)
def contact():
    form = ContactForm()
 
    if form.validate_on_submit():
        contact_history = ContactHistory(
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
 
    recruitment_tags = get_recruitment_tag_map([recruitment.id]).get(recruitment.id, [])

    return render_template(
        "natyukatu/recruitment_detail.html",
        recruitment=recruitment,
        recruitment_tags=recruitment_tags,
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
        if recruitment.application_start_at and datetime.now() < recruitment.application_start_at:
            flash("募集開始前のため申し込みできません")
            return redirect(url_for("natyukatu.recruitment_detail", recruitment_id=recruitment_id))
        if recruitment.application_end_at < datetime.now():
            flash("募集期間が終了しています")
            return redirect(url_for(
                "natyukatu.recruitment_detail",
                recruitment_id=recruitment_id
            ))
 
        requested_count = form.participant_count.data or 1
        accepted_entries = ParticipationHistory.query.filter_by(
            recruitment_id=recruitment_id
        ).all()
        occupied = sum(
            item.participant_count or 1
            for item in accepted_entries
            if not item.status or item.status.status_name != "否"
        )
        if occupied + requested_count > recruitment.capacity:
            flash("募集人数を超えるため申し込みできません")
            return redirect(url_for("natyukatu.recruitment_detail", recruitment_id=recruitment_id))

        entry = ParticipationHistory(
            recruitment_id=recruitment_id,
            user_id=get_user_id(),
            participant_count=requested_count,
            message=form.message.data,
            status_id=4,
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
@dt.route("/participation_application_already/<recruitment_id>", methods=["GET"])
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
        histories=histories,
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

    form = RecruitmentUpdateForm()

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

        update_photos = [
            photo for photo in (form.photo.data or [])
            if photo and getattr(photo, "filename", "")
        ]
        if update_photos:
            allowed_extensions = {"jpg", "jpeg", "png"}
            for photo in update_photos:
                extension = photo.filename.rsplit(".", 1)[-1].lower()
                if extension not in allowed_extensions:
                    flash("画像はjpg、jpeg、png形式で選択してください")
                    return render_template("natyukatu/recruitment_update.html", form=form, recruitment=recruitment)
            recruitment.photo = update_photos[0].read()
            recruitment.photo_mimetype = update_photos[0].mimetype or "image/jpeg"
            RecruitmentImage.query.filter_by(recruitment_id=recruitment.id).delete()
            for index, photo in enumerate(update_photos[1:], start=1):
                db.session.add(RecruitmentImage(
                    recruitment_id=recruitment.id,
                    image_data=photo.read(),
                    mimetype=photo.mimetype or "image/jpeg",
                    display_order=index
                ))

        if form.video.data and form.video.data.filename:
            extension = form.video.data.filename.rsplit(".", 1)[-1].lower()
            if extension not in {"mp4", "webm"}:
                flash("動画はMP4またはWebM形式を選択してください")
                return render_template("natyukatu/recruitment_update.html", form=form, recruitment=recruitment)
            recruitment.video = form.video.data.read()
            recruitment.video_mimetype = form.video.data.mimetype or "video/mp4"

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

# 参加辞退（確認画面表示 & 辞退処理）
@dt.route("/participation_quit/<int:recruitment_id>", methods=["GET", "POST"])
@login_required
def participation_quit(recruitment_id):
    recruitment = get_recruitment(recruitment_id)
    user_id = get_user_id()

    # 自分の参加履歴を取得
    history = ParticipationHistory.query.filter_by(
        user_id=user_id,
        recruitment_id=recruitment.id,
    ).first()

    if history is None:
        flash("参加履歴が見つかりませんでした。")
        return redirect(url_for("natyukatu.recruitment_history"))

    form = ParticipationQuitForm()

    # POST送信 かつ CSRF検証OKの場合
    if form.validate_on_submit():
        # ※ステータス更新方式の場合（「辞退」のStatusレコードを取得）
        quit_status = Status.query.filter_by(id=5).first()  
        if quit_status is None:
            flash("辞退ステータスの設定が見つかりません。")
            return redirect(url_for("natyukatu.recruitment_history"))

        try:
            history.status_id = quit_status.id
            db.session.commit()
            flash("参加を辞退しました。")
            return redirect(url_for("natyukatu.participation_quit_complete"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("辞退処理に失敗しました。時間をおいて再度お試しください。")
            return redirect(url_for("natyukatu.recruitment_history"))

    # GETアクセス時は確認画面を表示
    return render_template(
        "natyukatu/participation_quit.html",
        recruitment=recruitment,
        history=history,
        form=form,
    )

# 参加辞退完了画面
@dt.route("/participation_quit_complete")
@login_required
def participation_quit_complete():
    return render_template("natyukatu/participation_quit_complete.html")

#活動用画面
@dt.route("/application_management/<int:recruitment_id>")
@login_required
def application_management(recruitment_id):
    recruitment = get_recruitment(recruitment_id)
    if recruitment.user_id != get_user_id():
        abort(403)
    entries = ParticipationHistory.query.filter_by(
        recruitment_id=recruitment_id
    ).order_by(ParticipationHistory.added_at.desc()).all()
    return render_template(
        "natyukatu/application_management.html",
        recruitment=recruitment,
        entries=entries
    )


@dt.route("/applicant_decision/<int:applicant_id>", methods=["POST"])
@login_required
def applicant_decision(applicant_id):
    entry = ParticipationHistory.query.get_or_404(applicant_id)
    recruitment = get_recruitment(entry.recruitment_id)
    if recruitment.user_id != get_user_id():
        abort(403)
    decision = request.form.get("status")
    if decision not in {"可", "否"}:
        abort(400)
    status = Status.query.filter_by(status_name=decision).first()
    if status is None:
        status = Status(status_name=decision)
        db.session.add(status)
        db.session.flush()
    entry.status_id = status.id
    db.session.commit()
    flash(f"申込を「{decision}」に変更しました")
    return redirect(url_for("natyukatu.application_management", recruitment_id=recruitment.id))


@dt.route("/for_active/<recruitment_id>", methods=["GET", "POST"])
@login_required
def for_active(recruitment_id):
    # 募集情報を取得
    recruitment = get_recruitment(recruitment_id)
    user_id = get_user_id()

    # 募集者本人、または参加承認済みのユーザーだけアクセス可能
    is_owner = recruitment.user_id == user_id
    approved_entry = ParticipationHistory.query.join(
        Status,
        ParticipationHistory.status_id == Status.id
    ).filter(
        ParticipationHistory.recruitment_id == recruitment.id,
        ParticipationHistory.user_id == user_id,
        Status.status_name == "可"
    ).first()

    if not is_owner and approved_entry is None:
        abort(403)

    # メッセージ投稿フォーム
    form = MessageForm()

    # POSTリクエスト時の処理分岐
    if request.method == "POST":
        # メッセージ投稿ボタンが押された場合
        if form.submit.name in request.form:
            if form.validate_on_submit():
                message = ActiveMessage(
                    recruitment_id=recruitment.id,
                    user_id=user_id,
                    message=form.message.data,
                )
                db.session.add(message)
                db.session.commit()
                flash("メッセージを投稿しました")
                return redirect(url_for(
                    "natyukatu.for_active",
                    recruitment_id=recruitment.id
                ))

        # 参加者削除ボタンが押された場合
        elif "delete_participation" in request.form:
            # 参加者の削除は募集者本人だけ可能
            if not is_owner:
                abort(403)

            participation_id = request.form.get("participation_id")
            entry = ParticipationHistory.query.filter_by(
                id=participation_id,
                recruitment_id=recruitment.id
            ).first_or_404()

            db.session.delete(entry)
            db.session.commit()
            flash("申込者を削除しました")
            return redirect(url_for(
                "natyukatu.for_active",
                recruitment_id=recruitment.id
            ))

    # 参加者一覧を取得
    entries = ParticipationHistory.query.filter_by(
        recruitment_id=recruitment.id
    ).all()
    messages = ActiveMessage.query.filter_by(
        recruitment_id=recruitment.id
    ).order_by(ActiveMessage.post_at.asc()).all()

    return render_template(
        "natyukatu/for_active.html",
        recruitment=recruitment,
        entries=entries,
        messages=messages,
        form=form,
    )


#参加者を一覧から削除
def delete_participation(participation_id):
    entry = participation_history.query.filter_by(
        id=participation_id
    ).first_or_404()
 
    recruitment = get_recruitment(entry.recruitment_id)
 
    if recruitment.user_id != get_user_id():
        abort(403)
 
    db.session.delete(entry)
    db.session.commit()
 
    flash("申込者を削除しました")
 
#活動用メッセージ投稿
def messages(recruitment_id):
    recruitment = get_recruitment(recruitment_id)
    form = MessageForm()
 
    if form.validate_on_submit():
        message = ActiveMessage(
            user_id=get_user_id(),
            message=form.message.data,
        )
 
        db.session.add(message)
        db.session.commit()
 
        flash("メッセージを投稿しました")

#サンクスボタン
@dt.route("/thanks/<active_id>/<user_id>", methods=["POST"])
@login_required
def thanks(active_id, user_id):
    recruitment = get_recruitment(active_id)
    if recruitment.user_id != get_user_id():
        abort(403)

    entry = ParticipationHistory.query.filter_by(
        recruitment_id=active_id,
        user_id=user_id
    ).first_or_404()
    if entry.thanks_sent:
        flash("この参加者にはすでにありがとうを送っています")
        return redirect(url_for("natyukatu.for_active", recruitment_id=active_id))

    recipient = User.query.get_or_404(user_id)
    recipient.tanks_point = (recipient.tanks_point or 0) + 1
    entry.thanks_sent = True
    db.session.commit()
    flash("サンクスポイントを送りました")
    return redirect(url_for("natyukatu.for_active", recruitment_id=active_id))



#ランキング生成
@dt.route("/ranking")
def ranking():
    results = User.query.filter(
        User.tanks_point > 0
    ).order_by(
        User.tanks_point.desc(),
        User.nickname.asc()
    ).all()
    return render_template("natyukatu/ranking.html", rankings=results)


@dt.route(
    "/admin/recruitments/<active_id>/delete",
    methods=["POST"]
)
@login_required
def admin_delete_recruitment(active_id):
    if getattr(current_user, "role", None) != 1:
        abort(403)
    recruitment = get_recruitment(active_id)
 
    db.session.delete(recruitment)
    db.session.commit()
 
    flash("募集を削除しました")
 
    return redirect(url_for("natyukatu.admin"))
 
 
@dt.route("/admin")
@login_required
def admin():
    if getattr(current_user, "role", None) != 1:
        abort(403)
    recruitments = Recruitment.query.order_by(Recruitment.created_at.desc()).all()
    entries = ParticipationHistory.query.order_by(ParticipationHistory.added_at.desc()).all()
    users = User.query.order_by(User.id.asc()).all()
    return render_template(
        "natyukatu/admin.html",
        recruitments=recruitments,
        entries=entries,
        users=users
    )


# 時間での情報更新(1:募集中 2:募集終了 4:参加中 6:活動終了)
@dt.before_request
def auto_update_statuses():
    """画面遷移のたびに期限切れの募集・参加ステータスを自動更新する"""
    now = datetime.now()
    updated = False

    # 募集終了時間（application_end_at）を過ぎた募集を「募集終了（2）」にする
    expired_recruitments = Recruitment.query.filter(
        Recruitment.application_end_at <= now,
        Recruitment.status == 1,
    ).all()

    for rec in expired_recruitments:
        rec.status = 2
        updated = True

    # 活動終了時間（end_at）を過ぎた「参加中（4）」の参加履歴を「活動終了（6）」にする
    expired_histories = (
        ParticipationHistory.query.join(Recruitment)
        .filter(
            Recruitment.end_at <= now,
            ParticipationHistory.status_id == 4,
        )
        .all()
    )

    for hist in expired_histories:
        hist.status_id = 6
        updated = True

    # 変更があった場合のみコミットする
    if updated:
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()