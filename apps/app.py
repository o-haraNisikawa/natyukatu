
from pathlib import Path

import click

from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

from apps.config import config


# =====================================
# Flask拡張機能
# =====================================

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()

login_manager.login_view = "auth.login"
login_manager.login_message = ""


# =====================================
# Flaskアプリケーション作成
# =====================================

def create_app(config_key):
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY="2AZSMss3p5QPbcY2hBsj",

        SQLALCHEMY_DATABASE_URI=(
            f"sqlite:///{Path(__file__).parent.parent / 'local.sqlite'}"
        ),

        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ECHO=True,

        WTF_CSRF_SECRET_KEY="AuwzyszU5sugKN7KZs6f",
    )

    # 設定ファイルの読み込み
    app.config.from_object(config[config_key])

    # エラーハンドラー
    app.register_error_handler(
        404,
        page_not_found
    )

    app.register_error_handler(
        500,
        internal_server_error
    )

    # 拡張機能の初期化
    db.init_app(app)
    Migrate(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    # =================================
    # Blueprint登録
    # =================================

    from apps.crud import views as crud_views

    app.register_blueprint(
        crud_views.crud,
        url_prefix="/crud"
    )

    from apps.auth import views as auth_views

    app.register_blueprint(
        auth_views.auth,
        url_prefix="/auth"
    )

    from apps.natyukatu import views as dt_views

    app.register_blueprint(
        dt_views.dt
    )

    # =================================
    # CLIコマンド登録
    # =================================

    register_commands(app)

    return app


# =====================================
# 管理者登録コマンド
# =====================================

@click.command("create-admin")
def create_admin():
    """ターミナルから管理者アカウントを作成する"""

    from apps.crud.models import User

    # Flask CLIがアプリケーションコンテキストを提供

    click.echo("==============================")
    click.echo(" なちゅ活 管理者アカウント登録")
    click.echo("==============================")

    # ユーザー情報入力
    username = click.prompt(
        "ユーザー名"
    ).strip()

    nickname = click.prompt(
        "ニックネーム"
    ).strip()

    age = click.prompt(
        "年齢",
        type=click.IntRange(min=0, max=150)
    )

    email = click.prompt(
        "メールアドレス"
    ).strip()

    phone_number = click.prompt(
        "電話番号"
    ).strip()

    password = click.prompt(
        "パスワード",
        hide_input=True,
        confirmation_prompt=True
    )

    # メールアドレスの重複確認
    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user is not None:
        click.echo(
            "エラー：このメールアドレスは既に登録されています。"
        )
        return

    # 管理者アカウント作成
    user = User(
        username=username,
        nickname=nickname,
        age=age,
        email=email,
        password=password,
        phone_number=phone_number,

        # 管理者
        role=1,

        # 管理者は承認済み
        is_approved=True,

        # 初期ポイント
        tanks_point=0,

        # 団体情報
        group_name="",
        representative_name="",
        contact_email="",
        group_type=""
    )

    try:
        db.session.add(user)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        click.echo(
            f"管理者登録に失敗しました: {e}",
            err=True
        )
        raise click.ClickException(
            "データベースへの登録に失敗しました。"
        ) from e

    click.echo("")
    click.echo("==============================")
    click.echo(" 管理者登録が完了しました！")
    click.echo("==============================")
    click.echo(f"ユーザー名：{username}")
    click.echo(f"ニックネーム：{nickname}")
    click.echo(f"メールアドレス：{email}")
    click.echo("権限：管理者")
    click.echo("承認状態：承認済み")


# =====================================
# CLIコマンド登録
# =====================================

def register_commands(app):
    app.cli.add_command(create_admin)


# =====================================
# 404エラーハンドラー
# =====================================

def page_not_found(e):
    """404 Not Found"""
    return render_template(
        "404.html"
    ), 404


# =====================================
# 500エラーハンドラー
# =====================================

def internal_server_error(e):
    """500 Internal Server Error"""
    return render_template(
        "500.html"
    ), 500
