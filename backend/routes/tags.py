"""标签接口"""

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from models import LogTag, Tag, db

tags_bp = Blueprint("tags", __name__, url_prefix="/api/tags")


@tags_bp.route("/", methods=["GET"])
def list_tags():
    """获取所有标签，附带关联日志数量，按 log_count 降序"""
    rows = (
        db.session.query(Tag, func.count(LogTag.log_id).label("log_count"))
        .outerjoin(LogTag, Tag.id == LogTag.tag_id)
        .group_by(Tag.id)
        .order_by(func.count(LogTag.log_id).desc())
        .all()
    )

    data = [
        {**tag.to_dict(), "log_count": log_count}
        for tag, log_count in rows
    ]
    return jsonify(code=0, data=data, msg="ok")


@tags_bp.route("/", methods=["POST"])
def create_tag():
    """新建标签

    Body (JSON):
        name — 标签名（去除首尾空格）
    若标签已存在，直接返回已有标签，不报错。
    """
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()

    if not name:
        return jsonify(code=400, data=None, msg="标签名不能为空"), 400

    existing = Tag.query.filter_by(name=name).first()
    if existing:
        return jsonify(code=0, data=existing.to_dict(), msg="标签已存在，返回已有记录")

    tag = Tag(name=name)
    db.session.add(tag)
    db.session.commit()

    return jsonify(code=0, data=tag.to_dict(), msg="创建成功"), 201


@tags_bp.route("/<int:tag_id>", methods=["DELETE"])
def delete_tag(tag_id: int):
    """删除标签，同步删除所有 LogTag 关联"""
    tag = Tag.query.get(tag_id)
    if tag is None:
        return jsonify(code=404, data=None, msg="标签不存在"), 404

    # 删除关联记录
    LogTag.query.filter_by(tag_id=tag_id).delete()
    db.session.delete(tag)
    db.session.commit()

    return jsonify(code=0, data=None, msg="删除成功")
