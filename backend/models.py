"""数据库模型 — Log / Tag / LogTag"""

from datetime import date, datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Log(db.Model):
    """学习日志"""

    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, default="")
    content = db.Column(db.Text, nullable=False, default="")
    duration = db.Column(db.Integer, nullable=False, default=0)  # 学习时长（分钟）
    date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关联 LogTag，级联删除
    log_tags = db.relationship(
        "LogTag", backref="log", cascade="all, delete-orphan", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "duration": self.duration,
            "date": self.date.isoformat() if self.date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": [lt.tag.to_dict() for lt in self.log_tags.all()],
        }

    def __repr__(self):
        return f"<Log {self.id} {self.title!r}>"


class Tag(db.Model):
    """标签"""

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    log_tags = db.relationship(
        "LogTag", backref="tag", cascade="all, delete-orphan", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }

    def __repr__(self):
        return f"<Tag {self.id} {self.name!r}>"


class LogTag(db.Model):
    """日志-标签 多对多关联"""

    __tablename__ = "log_tags"

    log_id = db.Column(db.Integer, db.ForeignKey("logs.id"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"), primary_key=True)
