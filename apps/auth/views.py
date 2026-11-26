
from apps.app import db
from apps.auth.forms import SignUpForm, LoginForm
from apps.crud.models import User

from flask import (
    Blueprint,
    render_template,
    flash,
    url_for,
    redirect,
    request,
    abort,
)

from flask_login import login_user, logout_user


auth = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    static_folder="static"
)


# ログイン・新規登録トップ
@auth.route("/")
def index():
    return render_template("auth/index.html")


# 新規登録
@auth.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():

        # 一般登録では管理者権限を付与できない
        if form.role.data not in (2, 3):
            abort(403)

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            age=form.age.data,
            phone_number=form.phone_number.data,
            nickname=form.nickname.data,
            role=form.role.data,

            # 募集者は管理者承認待ち、参加者は即時利用可能
            is_approved=(form.role.data == 3),

            tanks_point=0,
            group_name="",
            representative_name="",
            contact_email="",
            group_type="",
        )

        # メールアドレス重複チェック
        if user.is_duplicate_email():
            flash("指定のメールアドレスは登録済みです")
            return redirect(url_for("auth.signup"))

        # DB登録
        db.session.add(user)
        db.session.commit()

        # 募集者の場合
        if user.role == 2:
            flash(
                "募集者として仮登録しました。"
                "管理者の承認後にログインできます。"
            )
            return redirect(url_for("auth.login"))

        # 参加者の場合は即時ログイン
        login_user(user)

        next_ = request.args.get("next")

        if next_ is None or not next_.startswith("/"):
            next_ = url_for("natyukatu.top")

        return redirect(next_)

    return render_template("auth/signup.html", form=form)


# ログイン
@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        # メールアドレスからユーザーを取得
        user = User.query.filter_by(
            email=form.email.data
        ).first()

        # ユーザーとパスワードの確認
        if user is not None and user.verify_password(
            form.password.data
        ):

            # 管理者の承認確認
            if not user.is_approved:
                flash(
                    "現在、管理者の承認待ちです。"
                    "承認後にログインできます。"
                )
                return render_template(
                    "auth/login.html",
                    form=form
                )

            login_user(user)
            return redirect(url_for("natyukatu.top"))

        flash("メールアドレスかパスワードが不正です")

    return render_template("auth/login.html", form=form)


# ログアウト
@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("natyukatu.top"))
