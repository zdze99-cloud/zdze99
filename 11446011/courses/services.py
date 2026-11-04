"""選課業務規則:檢核、加退選、志願分發、授權碼。

views.py 只負責接 request / 回 response,規則集中在這裡,方便測試。
"""
import random
from dataclasses import dataclass
from datetime import datetime

from django.db import transaction
from django.db.models import F, Max

from .models import AddRequest, Course, Enrollment, HistoryLog, Registration, Setting

STAGE = {1: "第一階段", 2: "第二階段", 3: "特殊加選"}
CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


@dataclass
class Check:
    name: str
    ok: bool
    note: str
    skip: bool = False

    @property
    def mark(self):
        return "–" if self.skip else ("✓" if self.ok else "✕")


@dataclass
class Result:
    ok: bool
    message: str


def gen_code():
    s = "".join(random.choice(CODE_CHARS) for _ in range(8))
    return f"{s[:4]}-{s[4:]}"


def log(student, action, course, ok, result):
    seq = (HistoryLog.objects.filter(student=student).aggregate(m=Max("seq"))["m"] or 0) + 1
    HistoryLog.objects.create(
        student=student,
        at=datetime.now().strftime("%m/%d %H:%M"),
        stage=STAGE[Setting.get().phase],
        action=action,
        course=str(course),
        ok=ok,
        result=result,
        seq=seq,
    )


def enrolled_courses(student):
    return [e.course for e in student.enrollments.select_related("course").order_by("id")]


def total_credits(courses):
    return sum(c.credits for c in courses)


def mode_for(course, phase):
    if phase == 1:
        return "lottery"
    if phase == 3 and (course.needs_code or course.is_full):
        return "bypass"
    return "normal"


def check(student, course, mode):
    """回傳這門課的各項檢核結果(開課、學分、衝堂、先修、名額、授權碼)。"""
    setting = Setting.get()
    others = [c for c in enrolled_courses(student) if c.pk != course.pk]
    total = total_credits(others) + course.credits
    conflict = next((c for c in others if c.overlaps(course)), None)
    pre_ok = not course.prereq or course.prereq in student.completed
    pre_name = student.completed.get(course.prereq, "")

    items = [
        Check("開課狀態", course.is_open, "正常開課" if course.is_open else "本課程已停開"),
        Check("學分上限", total <= setting.max_credits, f"選後 {total} 學分 / 上限 {setting.max_credits}"),
        Check("衝堂檢查", conflict is None, f"與「{conflict.name}」時間重疊" if conflict else "無時間衝突"),
        Check(
            "先修條件",
            pre_ok,
            f"需先修 {course.prereq} {pre_name}（{'已修畢' if pre_ok else '未修畢，擋修'}）"
            if course.prereq
            else "無先修限制",
        ),
    ]
    if mode == "lottery":
        items.append(
            Check("名額", True, f"已登記 {course.enrolled_count + 18} 人 / 上限 {course.capacity}，截止後抽籤", skip=True)
        )
    elif mode == "bypass":
        items.append(Check("名額", True, f"{course.enrolled_count}/{course.capacity}，授權碼可超收", skip=True))
    else:
        items.append(
            Check(
                "名額",
                not course.is_full,
                f"尚餘 {course.seats_left} 位（{course.enrolled_count}/{course.capacity}）"
                if not course.is_full
                else f"已額滿（{course.enrolled_count}/{course.capacity}）",
            )
        )
        items.append(
            Check(
                "授權碼",
                not course.needs_code,
                "需教師核發授權碼，請於特殊加選階段輸入" if course.needs_code else "不需授權碼",
            )
        )
    return items


@transaction.atomic
def enroll(student, course, mode="normal", via="加選"):
    failed = next((i for i in check(student, course, mode) if not i.ok), None)
    if failed:
        log(student, via, course, False, failed.name + "不符")
        return Result(False, f"加選失敗 · {failed.name}：{failed.note}")
    Enrollment.objects.get_or_create(student=student, course=course)
    Course.objects.filter(pk=course.pk).update(enrolled_count=F("enrolled_count") + 1)
    log(student, via, course, True, "成功")
    return Result(True, f"已加選「{course.name}」")


@transaction.atomic
def drop(student, course):
    deleted, _ = Enrollment.objects.filter(student=student, course=course).delete()
    if not deleted:
        return Result(False, "您沒有選這門課")
    Course.objects.filter(pk=course.pk, enrolled_count__gt=0).update(enrolled_count=F("enrolled_count") - 1)
    log(student, "退選", course, True, "成功")
    left = total_credits(enrolled_courses(student))
    minimum = Setting.get().min_credits
    if left < minimum:
        return Result(False, f"已退選「{course.name}」· 目前 {left} 學分，低於最低 {minimum} 學分")
    return Result(True, f"已退選「{course.name}」")


def register(student, course):
    """第一階段:登記 / 取消志願。"""
    existing = Registration.objects.filter(student=student, course=course)
    if existing.exists():
        existing.delete()
        return Result(True, f"已取消登記「{course.name}」")
    failed = next(
        (i for i in check(student, course, "lottery") if not i.ok and i.name in ("先修條件", "開課狀態")), None
    )
    if failed:
        return Result(False, f"無法登記 · {failed.note}")
    Registration.objects.create(student=student, course=course)
    order = student.registrations.count()
    log(student, "登記志願", course, True, "已登記")
    return Result(True, f"已登記第 {order} 志願「{course.name}」")


@transaction.atomic
def run_lottery(student):
    regs = list(student.registrations.select_related("course"))
    if not regs:
        return Result(False, "尚未登記任何志願")
    won = 0
    for reg in regs:
        course = Course.objects.get(pk=reg.course_id)
        failed = next((i for i in check(student, course, "lottery") if not i.ok), None)
        lucky = random.random() < (0.3 if course.is_full else 0.8)
        if not failed and lucky:
            Enrollment.objects.get_or_create(student=student, course=course)
            Course.objects.filter(pk=course.pk).update(enrolled_count=F("enrolled_count") + 1)
            log(student, "分發", course, True, "中籤")
            won += 1
        else:
            log(student, "分發", course, False, failed.name + "不符" if failed else "未中籤")
    student.registrations.all().delete()
    return Result(True, f"分發完成：中籤 {won} 門，未中籤 {len(regs) - won} 門")


@transaction.atomic
def use_code(student, course, code):
    code = code.strip().upper()
    req = AddRequest.objects.filter(course=course, sid=student.sid, status="approved", code=code).first()
    if not req:
        log(student, "授權碼加選", course, False, "授權碼無效")
        return Result(False, "授權碼無效或不屬於您")
    result = enroll(student, course, "bypass", "授權碼加選")
    if result.ok:
        req.status = "used"
        req.save(update_fields=["status"])
    return result


def issue_codes(requests):
    """核發授權碼。requests 是 AddRequest queryset(呼叫端先限縮成自己課程的申請)。"""
    n = 0
    for r in requests.filter(status="pending"):
        r.status, r.code = "approved", gen_code()
        r.save(update_fields=["status", "code"])
        n += 1
    return n


def request_block_reason(student, course):
    """回傳不能申請加簽的原因;可以申請則回傳 None。"""
    if not course.is_open:
        return "本課程已停開"
    if not (course.needs_code or course.is_full):
        return "本課程尚有名額且不需授權碼，可直接加選"
    if student.enrollments.filter(course=course).exists():
        return "您已選上這門課"
    if AddRequest.objects.filter(course=course, sid=student.sid).exists():
        return "您已送出過這門課的加簽申請"
    return None


def submit_request(student, course, reason):
    blocked = request_block_reason(student, course)
    if blocked:
        return Result(False, f"無法申請加簽 · {blocked}")
    AddRequest.objects.create(
        course=course, student=student, name=student.name, sid=student.sid,
        dept=f"{student.dept} {student.year} 年級", reason=reason,
    )
    log(student, "申請加簽", course, True, "待教師審核")
    return Result(True, f"已送出「{course.name}」的加簽申請，請等候教師審核")


# ---- 課表 / 畢業檢核 ----

PERIODS = [
    ("08:10", "09:00"), ("09:10", "10:00"), ("10:20", "11:10"), ("11:20", "12:10"), ("12:20", "13:10"),
    ("13:20", "14:10"), ("14:20", "15:10"), ("15:30", "16:20"), ("16:30", "17:20"), ("17:30", "18:20"),
]
DAYS = ["一", "二", "三", "四", "五", "六", "日"]

# (類別, 應修學分, 已修學分) —— 與原型相同的示範值
GRAD_REQ = [
    ("系必修", 60, 41), ("系選修", 30, 15), ("通識·人文", 4, 2), ("通識·社會", 4, 2),
    ("通識·自然", 4, 0), ("體育", 4, 3), ("自由選修", 22, 21),
]
GRAD_TOTAL = 128


def period_label(periods):
    return f"{periods[0]}–{periods[-1]}" if len(periods) > 1 else str(periods[0])


def time_range(periods):
    return f"{PERIODS[periods[0] - 1][0]}–{PERIODS[periods[-1] - 1][1]}"


def format_slots(course):
    return "、".join(f"{DAYS[d - 1]} {period_label(ps)}" for d, ps in course.day_periods())


def graduation(student):
    mine = enrolled_courses(student)

    def in_progress(key):
        total = 0
        for c in mine:
            if (
                (key == "系必修" and c.type == "必修")
                or (key == "系選修" and c.type == "選修")
                or key == f"{c.type}·{c.area}"
                or (key == "體育" and c.type == "體育")
            ):
                total += c.credits
        return total

    rows, earned_sum, prog_sum = [], 0, 0
    for key, req, earned in GRAD_REQ:
        prog = min(in_progress(key), max(0, req - earned))
        earned_sum += min(earned, req)
        prog_sum += prog
        if earned >= req:
            status, cls = "已達成", "tag tag-neutral"
        elif earned + prog >= req:
            status, cls = "本學期可達成", "tag tag-outline"
        else:
            status, cls = f"尚缺 {req - earned - prog} 學分", "tag tag-accent"
        rows.append(
            {
                "key": key, "status": status, "cls": cls,
                "p1": min(100, earned / req * 100), "p2": prog / req * 100,
                "text": f"{earned}{' + ' + str(prog) if prog else ''} / {req}",
            }
        )
    return rows, earned_sum, prog_sum, max(0, GRAD_TOTAL - earned_sum - prog_sum)
