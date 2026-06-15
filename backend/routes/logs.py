"""日志 CRUD 接口"""

from datetime import date, datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from models import Log, LogTag, Tag, db

logs_bp = Blueprint("logs", __name__, url_prefix="/api/logs")


# ── 辅助函数 ────────────────────────────────────────────────

def _format_log(log: Log) -> dict:
    """格式化单条日志，包含标签列表"""
    return log.to_dict()


def _sync_tags(log: Log, tag_names: list[str]):
    """同步日志的标签关联：清除旧关联 → 按名称查找/创建标签 → 建立新关联"""
    # 清洗：去空白、去重、去空
    tag_names = list({t.strip() for t in tag_names if t and t.strip()})

    # 删除旧关联
    LogTag.query.filter_by(log_id=log.id).delete()

    for name in tag_names:
        tag = Tag.query.filter_by(name=name).first()
        if tag is None:
            tag = Tag(name=name)
            db.session.add(tag)
            db.session.flush()  # 拿到 tag.id
        db.session.add(LogTag(log_id=log.id, tag_id=tag.id))


# ── 路由 ────────────────────────────────────────────────────

@logs_bp.route("/", methods=["GET"])
def list_logs():
    """获取日志列表，支持筛选与分页

    Query params:
        q      — 关键词，模糊匹配 title 和 content
        tag    — 标签名精确筛选
        date   — 精确日期 (YYYY-MM-DD)
        page   — 页码，默认 1
        limit  — 每页条数，默认 10
    """
    q = request.args.get("q", "").strip()
    tag_name = request.args.get("tag", "").strip()
    date_str = request.args.get("date", "").strip()
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)

    query = Log.query

    # 关键词模糊搜索
    if q:
        query = query.filter(
            or_(Log.title.contains(q), Log.content.contains(q))
        )

    # 标签名筛选
    if tag_name:
        query = query.join(LogTag).join(Tag).filter(Tag.name == tag_name)

    # 精确日期筛选
    if date_str:
        try:
            query = query.filter(Log.date == date.fromisoformat(date_str))
        except ValueError:
            return jsonify(code=400, data=None, msg="日期格式错误，请使用 YYYY-MM-DD"), 400

    pagination = query.order_by(Log.date.desc(), Log.created_at.desc()).paginate(
        page=page, per_page=limit, error_out=False
    )

    return jsonify(
        code=0,
        data={
            "items": [_format_log(log) for log in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "limit": limit,
            "pages": pagination.pages,
        },
        msg="ok",
    )


@logs_bp.route("/", methods=["POST"])
def create_log():
    """新建日志

    Body (JSON):
        title    — 标题（必填，非空）
        content  — Markdown 正文
        duration — 学习时长（分钟，非负整数）
        date     — 学习日期 (YYYY-MM-DD)，默认今天
        tags     — 标签名数组，如 ["Python", "算法"]
    """
    data = request.get_json(silent=True) or {}

    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    duration = data.get("duration", 0)
    date_str = (data.get("date") or "").strip()
    tag_names = data.get("tags") or []

    if not title:
        return jsonify(code=400, data=None, msg="标题不能为空"), 400

    try:
        log_date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        return jsonify(code=400, data=None, msg="日期格式错误，请使用 YYYY-MM-DD"), 400

    if not isinstance(duration, int) or duration < 0:
        return jsonify(code=400, data=None, msg="学习时长必须为非负整数"), 400

    log = Log(title=title, content=content, duration=duration, date=log_date)
    db.session.add(log)
    db.session.flush()  # 获取 log.id

    _sync_tags(log, tag_names)

    db.session.commit()

    return jsonify(code=0, data=_format_log(log), msg="创建成功"), 201


@logs_bp.route("/<int:log_id>", methods=["GET"])
def get_log(log_id: int):
    """获取单条日志（含标签）"""
    log = Log.query.get(log_id)
    if log is None:
        return jsonify(code=404, data=None, msg="日志不存在"), 404
    return jsonify(code=0, data=_format_log(log), msg="ok")


@logs_bp.route("/<int:log_id>", methods=["PUT"])
def update_log(log_id: int):
    """更新日志（字段均可选，仅更新传入的字段）

    Body 字段同 create_log，但均非必填。
    传入 tags 时完成全量标签同步。
    """
    log = Log.query.get(log_id)
    if log is None:
        return jsonify(code=404, data=None, msg="日志不存在"), 404

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            return jsonify(code=400, data=None, msg="标题不能为空"), 400
        log.title = title

    if "content" in data:
        log.content = (data["content"] or "").strip()

    if "duration" in data:
        duration = data["duration"]
        if not isinstance(duration, int) or duration < 0:
            return jsonify(code=400, data=None, msg="学习时长必须为非负整数"), 400
        log.duration = duration

    if "date" in data:
        date_str = (data["date"] or "").strip()
        try:
            log.date = date.fromisoformat(date_str) if date_str else date.today()
        except ValueError:
            return jsonify(code=400, data=None, msg="日期格式错误，请使用 YYYY-MM-DD"), 400

    if "tags" in data:
        _sync_tags(log, data["tags"] or [])

    log.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify(code=0, data=_format_log(log), msg="更新成功")


@logs_bp.route("/<int:log_id>", methods=["DELETE"])
def delete_log(log_id: int):
    """删除日志，级联删除关联 LogTag"""
    log = Log.query.get(log_id)
    if log is None:
        return jsonify(code=404, data=None, msg="日志不存在"), 404
    db.session.delete(log)
    db.session.commit()
    return jsonify(code=0, data=None, msg="删除成功")
