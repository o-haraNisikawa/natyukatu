from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField,IntegerField,SubmitField,SelectField
from wtforms.validators import DataRequired, Email, Length

class SignUpForm(FlaskForm):
    username = StringField(
        "ユーザー名",
        validators=[
            DataRequired("ユーザ名は必須です。"),
            Length(1, 30, "30文字以内で入力してください。"),
            ],
    )
    email = StringField(
        "メールアドレス",
        validators=[
            DataRequired("メールアドレスは必須です。"),
            Email("メールアドレスの形式で入力してください。"),
        ],
    )
    password = PasswordField("パスワード",
        validators=[DataRequired("パスワードは必須です。")])
    age = IntegerField(
    "年齢",
    validators=[
        DataRequired("年齢は必須です。"),
        ],
    )
    phone_number = StringField(
    "電話番号",
    validators=[
        DataRequired("電話番号は必須です。"),
        Length(1, 30, ""),
        ],
    )
    nickname = StringField(
    "ニックネーム",
    validators=[
        DataRequired("ニックネームは必須です。"),
        Length(1, 30, "30文字以内で入力してください。"),
            ],
    )
    #ロール
    role = SelectField(
        choices=[
        (1, "管理者"),
        (2, "募集者"),
        (3, "参加者"),
        ],

    coerce=int,
    validators=[
        DataRequired("ステータスを選択してください。"),
    ],
    )
    
    submit = SubmitField("新規登録")

class LoginForm(FlaskForm):
    email = StringField(
        "メールアドレス",
        validators=[
            DataRequired("メールアドレスは必須です"),
            Email("メールアドレスの形式で入力してください"),
        ],
    )
    password = PasswordField("パスワード",validators=[DataRequired("パスワードは必須です")])
    submit = SubmitField("ログイン")