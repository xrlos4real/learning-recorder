"""统计接口"""

from datetime import date, timedelta

from flask import Blueprint, jsonify
from sqlalchemy import func

from models import Log, db

stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


@stats_bp.route("/heatmap", methods=["GET"])
def heatmap():
    """过去 365 天每天的日志条数

    返回:
        [{"date": "2026-06-14", "count": 2}, ...]
        没有记录的天不返回。
    """
    year_ago = date.today() - timedelta(days=364)

    rows = (
        db.session.query(Log.date, func.count(Log.id))
        .filter(Log.date >= year_ago)
        .group_by(Log.date)
        .order_by(Log.date.asc())
        .all()
    )

    data = [{"date": d.isoformat(), "count": c} for d, c in rows]
    return jsonify(code=0, data=data, msg="ok")


@stats_bp.route("/summary", methods=["GET"])
def summary():
    """汇总统计

    返回:
        total_logs    — 总日志条数
        total_duration — 总学习时长（分钟）
        streak        — 当前连续打卡天数
    """
    total_logs = db.session.query(func.count(func.distinct(Log.date))).scalar()

    total_duration = (
        db.session.query(func.coalesce(func.sum(Log.duration), 0)).scalar()
    )

    # 计算 streak：从今天往前数，连续有记录的天数
    streak = 0
    today = date.today()
    cursor = today
    while True:
        has_log = db.session.query(
            Log.query.filter(Log.date == cursor).exists()
        ).scalar()
        if not has_log:
            break
        streak += 1
        cursor = cursor - timedelta(days=1)

    return jsonify(
        code=0,
        data={
            "total_logs": total_logs,
            "total_duration": total_duration,
            "streak": streak,
        },
        msg="ok",
    )


@stats_bp.route("/daily", methods=["GET"])
def daily():
    """最近 30 天每天的学习时长之和

    返回:
        [{"date": "2026-06-14", "duration": 90}, ...]
        没有记录的天 duration 返回 0。
    """
    today = date.today()
    start = today - timedelta(days=29)

    rows = (
        db.session.query(Log.date, func.sum(Log.duration))
        .filter(Log.date >= start)
        .group_by(Log.date)
        .all()
    )

    # 建立日期 → 时长 映射
    duration_map = {d: dur for d, dur in rows}

    # 补零填充所有 30 天
    data = []
    for i in range(30):
        d = start + timedelta(days=i)
        data.append({
            "date": d.isoformat(),
            "duration": duration_map.get(d, 0),
        })

    return jsonify(code=0, data=data, msg="ok")
