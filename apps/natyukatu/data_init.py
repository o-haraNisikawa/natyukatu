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
    Status
)
from apps.app import db

def init_data():
    # いったん初期登録
    init = [
        # 業種 (tag_kinds=1)
        RecruitmentTag(tag_name="農業", tag_kinds=1),
        RecruitmentTag(tag_name="漁業", tag_kinds=1),
        RecruitmentTag(tag_name="林業", tag_kinds=1),

        # 都道府県 (tag_kinds=3)
        RecruitmentTag(tag_name="岩手県", tag_kinds=3),

        # 岩手県 市町村 (tag_kinds=4)
        # 市（14市）
        RecruitmentTag(tag_name="盛岡市", tag_kinds=4),
        RecruitmentTag(tag_name="宮古市", tag_kinds=4),
        RecruitmentTag(tag_name="大船渡市", tag_kinds=4),
        RecruitmentTag(tag_name="花巻市", tag_kinds=4),
        RecruitmentTag(tag_name="北上市", tag_kinds=4),
        RecruitmentTag(tag_name="久慈市", tag_kinds=4),
        RecruitmentTag(tag_name="遠野市", tag_kinds=4),
        RecruitmentTag(tag_name="一関市", tag_kinds=4),
        RecruitmentTag(tag_name="陸前高田市", tag_kinds=4),
        RecruitmentTag(tag_name="釜石市", tag_kinds=4),
        RecruitmentTag(tag_name="二戸市", tag_kinds=4),
        RecruitmentTag(tag_name="八幡平市", tag_kinds=4),
        RecruitmentTag(tag_name="奥州市", tag_kinds=4),
        RecruitmentTag(tag_name="滝沢市", tag_kinds=4),
        # 町（15町）
        RecruitmentTag(tag_name="雫石町", tag_kinds=4),
        RecruitmentTag(tag_name="葛巻町", tag_kinds=4),
        RecruitmentTag(tag_name="岩手町", tag_kinds=4),
        RecruitmentTag(tag_name="紫波町", tag_kinds=4),
        RecruitmentTag(tag_name="矢巾町", tag_kinds=4),
        RecruitmentTag(tag_name="西和賀町", tag_kinds=4),
        RecruitmentTag(tag_name="金ケ崎町", tag_kinds=4),
        RecruitmentTag(tag_name="平泉町", tag_kinds=4),
        RecruitmentTag(tag_name="住田町", tag_kinds=4),
        RecruitmentTag(tag_name="大槌町", tag_kinds=4),
        RecruitmentTag(tag_name="山田町", tag_kinds=4),
        RecruitmentTag(tag_name="岩泉町", tag_kinds=4),
        RecruitmentTag(tag_name="軽米町", tag_kinds=4),
        RecruitmentTag(tag_name="洋野町", tag_kinds=4),
        RecruitmentTag(tag_name="一戸町", tag_kinds=4),
        # 村（4村）
        RecruitmentTag(tag_name="田野畑村", tag_kinds=4),
        RecruitmentTag(tag_name="普代村", tag_kinds=4),
        RecruitmentTag(tag_name="野田村", tag_kinds=4),
        RecruitmentTag(tag_name="九戸村", tag_kinds=4),

        # ステータス
        Status(status_name="募集中"),
        Status(status_name="募集終了"),
        Status(status_name="参加申込中"),
        Status(status_name="参加中"),
        Status(status_name="辞退"),
        Status(status_name="参加済み"),
    ]

    db.session.add_all(init)
    db.session.commit()  # 最後にまとめてコミット

def delete():
    try:
        # テーブルの全件削除
        RecruitmentTag.query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"削除中にエラーが発生しました: {e}")
        raise e