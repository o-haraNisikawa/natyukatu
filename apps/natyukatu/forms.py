from flask_wtf.form import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed, MultipleFileField
from wtforms.fields import (
    StringField,
    PasswordField,
    TextAreaField,
    SelectField,
    IntegerField,
    DateTimeLocalField,
    FileField,
    HiddenField,
    BooleanField,
    SubmitField,
    SelectMultipleField,
    RadioField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    NumberRange,
    Optional,
    EqualTo,
)
 
 
class SearchForm(FlaskForm):
    # キーワード検索欄
    keyword = StringField(
        validators=[
            Optional(),
            Length(max=50)
        ]
    )
    # タグ選択欄
    tag_id = SelectMultipleField(
        choices=[],
        coerce=int
    )
    submit = SubmitField("検索する")
 
 
#お気に入り
class LikeForm(FlaskForm):
    recruitment_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField("お気に入り登録/解除")
 
#新規募集登録
class RecruitmentForm(FlaskForm):

    kind = RadioField(
        "募集種類",
        choices=[("#農業", "農業"), ("#漁業", "漁業"),("#林業","林業")],
        validators=[DataRequired()]
    )

    title = StringField(
        "募集タイトル",
        validators=[
            DataRequired(),
            Length(max=100)
        ]
    )

    description = TextAreaField(
        "募集内容",
        validators=[
            DataRequired(),
            Length(max=400)
        ]
    )

    photo = MultipleFileField(
        "募集画像（複数選択可能）",
        validators=[Optional()]
    )

    # 募集動画（任意）
    video = FileField(
        "募集動画（任意）",
        validators=[
            Optional(),
            FileAllowed(
                ["mp4", "webm"],
                "MP4またはWebM形式の動画を選択してください"
            )
        ]
    )

    tag = StringField(
        "タグ（スペース区切りで入力）",
        validators=[
            Optional()
        ])

    location_prefecture = SelectField(
            "都道府県",
            default="岩手県",
            validators=[
                DataRequired(),
            ]
        )

    location_city = SelectField(
        "市区町村",
        validators=[
            DataRequired(),
        ]
    )

    location_detail = StringField(
        "詳しい住所",
        validators=[
            DataRequired(),
            Length(max=100)
        ]
    )

    start_at = DateTimeLocalField(
        "活動開始日時",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()]
    )

    end_at = DateTimeLocalField(
        "活動終了日時",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()]
    )

    application_start_at = DateTimeLocalField(
        "募集開始日時",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()]
    )

    application_end_at = DateTimeLocalField(
        "募集終了日時",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()]
    )

    capacity = IntegerField(
        "募集人数",
        validators=[
            DataRequired(),
            NumberRange(min=1)
        ]
    )

    eligibility = StringField(
        "参加条件",
        validators=[
            DataRequired(),
            Length(max=100)
        ]
    )

    required_items = StringField(
        "持ち物",
        validators=[
            DataRequired(),
            Length(max=100)
        ]
    )

    submit = SubmitField("募集を登録")

#ユーザー退会
class WithdrawalForm(FlaskForm):
    password = PasswordField(
        "パスワード",
        validators=[DataRequired()]
    )

    confirm = BooleanField(
        "退会することに同意します",
        validators=[DataRequired(message="同意にチェックが必要です。")]
    )
    submit = SubmitField("退会する")


#お問い合わせ
class ContactForm(FlaskForm):
    name = StringField(
        "名前",
        validators=[
            DataRequired(),
            Length(max=20)
        ]
    )

    email = StringField(
        "メールアドレス",
        validators=[
            DataRequired(),
            Email(),
            Length(max=30)
        ]
    )

    subject = StringField(
        "お問い合わせ件名",
        validators=[
            DataRequired(),
            Length(max=30)
        ]
    )

    body = TextAreaField(
        "お問い合わせ内容",
        validators=[DataRequired()]
    )

    submit = SubmitField("送信する")


#参加申し込みフォーム
class ParticipationForm(FlaskForm):
    participant_count = IntegerField(
        "参加人数",
        validators=[
            DataRequired(),
            NumberRange(min=1)
        ]
    )

    message = TextAreaField(
        "応募メッセージ",
        validators=[
            Optional(),
            Length(max=500)
        ]
    )

    submit = SubmitField("参加申し込み")

#募集削除フォーム
class RecruitmentDeleteForm(FlaskForm):
    recruitment_id = HiddenField(
        "募集ID",
        validators=[DataRequired()]
    )

    confirm = BooleanField(
        "この募集を削除することに同意します",
        validators=[DataRequired()]
    )

    submit = SubmitField("募集を削除")

class ParticipationQuitForm(FlaskForm):
    """参加辞退の確認フォーム"""

    submit = SubmitField("辞退する")

#参加・募集履歴更新フォーム(分ける)
class HistoryUpdateForm(FlaskForm):
    status = SelectField(
        "履歴状態",
        choices=[
            ("募集中", "募集中"),
            ("受付終了", "受付終了"),
            ("参加予定", "参加予定"),
            ("参加済み", "参加済み"),
            ("キャンセル", "キャンセル")
        ],
        validators=[DataRequired()]
    )

    review_status = SelectField(
        "確認状態",
        choices=[
            ("未確認", "未確認"),
            ("確認済み", "確認済み")
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("履歴を更新")


#メッセージフォーム
class MessageForm(FlaskForm):
    message = StringField(
        "メッセージ",
        validators=[
            DataRequired(),
            Length(max=200)
        ]
    )

    submit = SubmitField("投稿する")

#申込者一覧・可否ボタンフォーム
class ApplicantDecisionForm(FlaskForm):
    applicant_id = HiddenField(
        "申込者ID",
        validators=[DataRequired()]
    )

    status = SelectField(
        "申込可否",
        choices=[
            ("可", "可"),
            ("否", "否")
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("決定する")

 
#ユーザー情報更新
class UserUpdateForm(FlaskForm):
    username = StringField(
        "ユーザー名",
        validators=[
            DataRequired(message="ユーザー名は必須です。"),
            Length(max=30, message="30文字以内で入力してください。"),
        ],
    )
    email = StringField(
        "メールアドレス",
        validators=[
            DataRequired(message="メールアドレスは必須です。"),
            Email(message="メールアドレスの形式で入力してください。"),
        ],
    )
    # 編集時は空欄でも通るように Optional() をつける（入力されたときだけ更新する想定）
    password = PasswordField(
        "パスワード（変更する場合のみ）",
        validators=[Optional()],
    )
    age = IntegerField(
        "年齢",
        validators=[DataRequired(message="必須です。")],
    )
    phone_number = StringField(
        "電話番号",
        validators=[DataRequired(message="必須です。")],
    )
    nickname = StringField(
        "ニックネーム",
        validators=[DataRequired(message="必須です。")],
    )
    submit = SubmitField("変更")
 
#募集更新
class RecruitmentUpdateForm(FlaskForm):
 
    kind = RadioField(
        "募集種類",
        choices=[("#農業", "農業"), ("#漁業", "漁業"),("#林業","林業")],
        validators=[DataRequired()]
    )
 
    title = StringField(
        "募集タイトル",
        validators=[
            DataRequired(),
            Length(max=100)
        ]
    )
 
    description = TextAreaField(
        "募集内容",
        validators=[
            DataRequired(),
            Length(max=400)
        ]
    )
 
    photo = MultipleFileField(
        "募集画像（複数選択可能）",
        validators=[Optional()]
    )
 
    # 募集動画（任意）
    video = FileField(
        "募集動画（任意）",
        validators=[
            Optional(),
            FileAllowed(
                ["mp4", "webm"],
                "MP4またはWebM形式の動画を選択してください"
            )
        ]
    )
 
    tag = StringField(
        "タグ（スペース区切りで入力）",
        validators=[
            Optional()
        ])
 
    location_prefecture = SelectField(
            "都道府県",
            default="岩手県",
            validators=[
                DataRequired(),
            ]
        )
 
    location_city = SelectField(
        "市区町村",
        validators=[
            DataRequired(),
        ]
    )
 
    location_detail = StringField(
        "詳しい住所",
        validators=[
            DataRequired(),
            Length(max=100)
        ]
    )
 
    start_at = DateTimeLocalField(
        "活動開始日時",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()]
    )
 
    end_at = DateTimeLocalField(
        "活動終了日時",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()]
    )
 
    application_start_at = DateTimeLocalField(
        "募集開始日時",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()]
    )
 
    application_end_at = DateTimeLocalField(
        "募集終了日時",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()]
    )
 
    capacity = IntegerField(
        "募集人数",
        validators=[
            DataRequired(),
            NumberRange(min=1)
        ]
    )
 
    eligibility = StringField(
        "参加条件",
        validators=[
            DataRequired(),
            Length(max=100)
        ]
    )
 
    required_items = StringField(
        "持ち物",
        validators=[
            DataRequired(),
            Length(max=100)
        ]
    )
 
    submit = SubmitField("募集を登録")
