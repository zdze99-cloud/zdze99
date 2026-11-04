import random
from datetime import date, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import services
from .context import NAV, role_of
from .forms import AddRequestForm
from .models import AddRequest, Course, Rule, Setting, Student, Wish
from .seed_data import G_DEF, PH_DATE, PH_DESC
from .services import DAYS, PERIODS

COURSE_TYPES = ["全部", "必修", "選修", "通識", "體育"]


def role_required(*roles):
    """登入後還要屬於指定角色(Django Group)才能進入。"""

    def deco(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            role = role_of(request.user)
            if role not in roles:
                if role is None:
                    raise PermissionDenied("此帳號尚未設定角色")
                messages.error(request, "目前身分無法使用此頁面，已回到你的首頁。")
                return redirect("courses:home")
            return view(request, *args, **kwargs)

        return wrapper

    return deco


student_required = role_required("student")


def me(request):
    student = Student.objects.filter(user=request.user).first()
    if student is None:
        raise PermissionDenied("此帳號沒有對應的學生資料")
    return student


def notify(request, result):
    (messages.success if result.ok else messages.error)(request, result.message)


def back(request, fallback="courses:search"):
    nxt = request.POST.get("next", "")
    # 只接受站內相對路徑，避免 open redirect
    if nxt.startswith("/") and not nxt.startswith("//"):
        return redirect(nxt)
    return redirect(fallback)


# ---- 登入 / 登出 / 階段 ----

class LoginView(auth_views.LoginView):
    template_name = "courses/login.html"
    redirect_authenticated_user = True
    # 登入頁的快速登入按鈕(展示用,密碼皆為示範密碼 1234)
    extra_context = {"quick_logins": [
        # (帳號, 角色, 姓名, 圖示, 顏色)
        ("11446011", "學生", "萬睿鈞", "student", "blue"),
        ("B11202045", "學生", "陳柏宇", "student", "teal"),
        ("lin", "教師", "林俊杰", "teacher", "green"),
        ("registrar", "教務處", "王秀蘭", "office", "amber"),
        ("sysadmin", "系統", "系統管理員", "system", "purple"),
    ]}


class LogoutView(auth_views.LogoutView):
    next_page = "courses:login"


@login_required
def home(request):
    role = role_of(request.user)
    if role is None:
        raise PermissionDenied("此帳號尚未設定角色")
    return redirect(f"courses:{NAV[role][0][0]}")


@require_POST
@role_required("admin")
def switch_phase(request):
    try:
        phase = int(request.POST.get("phase", ""))
    except ValueError:
        phase = 0
    if phase in (1, 2, 3):
        s = Setting.get()
        s.phase = phase
        s.save(update_fields=["phase"])
        messages.success(request, f"已切換為「{dict(Setting.PHASES)[phase]}」")
    return back(request, "courses:rules")


# ---- 學生:課程查詢 ----

def course_card(c, student, enrolled_codes, wish_codes, reg_codes, phase):
    """替 Course 掛上畫面用的 c.view 字典(按鈕文字、衝堂、擋修…)。"""
    mine = c.code in enrolled_codes
    if mine:
        label, cls = "退選", "btn btn-secondary"
    elif phase == 1:
        if c.code in reg_codes:
            label, cls = f"第 {reg_codes.index(c.code) + 1} 志願 ✓", "btn btn-secondary"
        else:
            label, cls = "登記志願", "btn btn-primary"
    elif phase == 3 and (c.needs_code or c.is_full):
        label, cls = "輸入授權碼", "btn btn-primary"
    else:
        label, cls = "加選", "btn btn-primary"
    conflict = not mine and any(c.overlaps(o) for o in Course.objects.filter(code__in=enrolled_codes))
    c.view = {
        "mine": mine, "label": label, "cls": cls, "conflict": conflict,
        "blocked": bool(c.prereq) and c.prereq not in student.completed,
        "starred": c.code in wish_codes, "time": services.format_slots(c),
        "seat_note": "停開" if not c.is_open else "額滿" if c.is_full else f"餘 {c.seats_left}",
    }
    return c


def student_state(student):
    return (
        list(student.enrollments.values_list("course__code", flat=True)),
        set(student.wishes.values_list("course__code", flat=True)),
        list(student.registrations.values_list("course__code", flat=True)),
    )


# 查無結果時,依序放寬這些條件(最不重要的先放寬),直到找到課程為止
RELAX_ORDER = [
    ("star", "只看收藏"), ("no_conflict", "不衝堂"), ("per", "節次"), ("day", "星期"), ("year", "年級"),
    ("bld", "大樓"), ("type", "類別"), ("dept", "系所"), ("q", "關鍵字"),
]
FILTER_DEFAULTS = {"", "0", "全部", "全部系所", "全部大樓"}


def filter_cards(q, student, setting, state):
    """依查詢條件 q 篩選課程,回傳掛好 c.view 的課程清單。"""
    enrolled_codes, wish_codes, reg_codes = state
    qs = Course.objects.all()
    text = q.get("q", "").strip()
    if text:
        qs = qs.filter(
            Q(code__icontains=text) | Q(name__icontains=text) | Q(teacher__icontains=text)
            | Q(room__icontains=text) | Q(building__icontains=text)
        )
    if q.get("dept") and q["dept"] != "全部系所":
        qs = qs.filter(dept=q["dept"])
    if q.get("type") and q["type"] != "全部":
        qs = qs.filter(type=q["type"])
    if q.get("bld") and q["bld"] != "全部大樓":
        qs = qs.filter(building=q["bld"])
    year = q.get("year", "0")
    if year.isdigit() and year != "0":
        qs = qs.filter(Q(year=0) | Q(year=int(year)))

    day, per = q.get("day", "0"), q.get("per", "0")
    cards = []
    for c in qs:
        if day != "0" and not any(str(d) == day for d, _ in c.day_periods()):
            continue
        if per.isdigit() and per != "0" and not any(int(per) in ps for _, ps in c.day_periods()):
            continue
        if q.get("star") and c.code not in wish_codes:
            continue
        card = course_card(c, student, enrolled_codes, wish_codes, reg_codes, setting.phase)
        if q.get("no_conflict") and card.view["conflict"] and not card.view["mine"]:
            continue
        cards.append(card)
    return cards


@student_required
def search(request):
    student, setting = me(request), Setting.get()
    q = request.GET
    state = student_state(student)
    reg_codes = state[2]
    cards = filter_cards(q, student, setting, state)

    # 保證一定有課:查無結果就逐一放寬條件,並告訴使用者放寬了哪些
    relaxed = []
    if not cards:
        loose = q.copy()
        for key, label in RELAX_ORDER:
            if loose.get(key, "").strip() in FILTER_DEFAULTS:
                continue
            loose.pop(key)
            relaxed.append(label)
            cards = filter_cards(loose, student, setting, state)
            if cards:
                break

    return render(request, "courses/search.html", {
        "cards": cards, "f": q, "types": COURSE_TYPES, "relaxed": relaxed,
        "depts": ["全部系所"] + list(Course.objects.order_by("dept").values_list("dept", flat=True).distinct()),
        "buildings": ["全部大樓"] + list(Course.objects.order_by("building").values_list("building", flat=True).distinct()),
        "days": [(str(i + 1), f"週{d}") for i, d in enumerate(DAYS)],
        "periods": [str(i) for i in range(1, 11)],
        "credits": services.total_credits(services.enrolled_courses(student)),
        "phase_desc": PH_DESC[str(setting.phase)], "phase_date": PH_DATE[str(setting.phase)],
        "registered": len(reg_codes), "next": request.get_full_path(),
    })


def render_detail(request, student, course, form=None, status=200):
    setting = Setting.get()
    enrolled_codes, wish_codes, reg_codes = student_state(student)
    course_card(course, student, enrolled_codes, wish_codes, reg_codes, setting.phase)
    mine = course.view["mine"]
    mode = "normal" if mine else services.mode_for(course, setting.phase)
    blocked = services.request_block_reason(student, course)
    return render(request, "courses/detail.html", {
        "c": course, "checks": services.check(student, course, mode),
        "need_code": not mine and setting.phase == 3 and (course.needs_code or course.is_full),
        "my_req": AddRequest.objects.filter(course=course, sid=student.sid).first(),
        "can_request": blocked is None, "form": form or AddRequestForm(),
        "grade": G_DEF.get(course.type, []), "next": request.GET.get("next", ""),
    }, status=status)


@student_required
def course_detail(request, code):
    return render_detail(request, me(request), get_object_or_404(Course, code=code))


@require_POST
@student_required
def course_request(request, code):
    student, course = me(request), get_object_or_404(Course, code=code)
    form = AddRequestForm(request.POST)
    if not form.is_valid():
        return render_detail(request, student, course, form=form, status=400)
    notify(request, services.submit_request(student, course, form.cleaned_data["reason"]))
    return redirect("courses:detail", code=code)


@require_POST
@student_required
def course_act(request, code):
    student, setting = me(request), Setting.get()
    course = get_object_or_404(Course, code=code)
    if student.enrollments.filter(course=course).exists():
        notify(request, services.drop(student, course))
    elif setting.phase == 1:
        notify(request, services.register(student, course))
    elif setting.phase == 3 and (course.needs_code or course.is_full):
        return redirect("courses:detail", code=code)
    else:
        notify(request, services.enroll(student, course))
    return back(request)


@require_POST
@student_required
def course_drop(request, code):
    notify(request, services.drop(me(request), get_object_or_404(Course, code=code)))
    return back(request, "courses:list")


@require_POST
@student_required
def course_star(request, code):
    course = get_object_or_404(Course, code=code)
    wish, created = Wish.objects.get_or_create(student=me(request), course=course)
    if not created:
        wish.delete()
    return back(request)


@require_POST
@student_required
def course_use_code(request, code):
    course = get_object_or_404(Course, code=code)
    notify(request, services.use_code(me(request), course, request.POST.get("code", "")))
    return redirect("courses:detail", code=code)


@require_POST
@student_required
def lottery(request):
    notify(request, services.run_lottery(me(request)))
    return redirect("courses:list")


# ---- 學生:課表 / 清單 / 檢核 / 紀錄 ----

@student_required
def schedule(request):
    courses = services.enrolled_courses(me(request))
    blocks, by_day = [], {d: [] for d in range(1, 8)}
    for c in courses:
        for d, ps in c.day_periods():
            blocks.append({"row": f"{ps[0] + 1} / span {len(ps)}", "col": d + 1, "course": c})
            by_day[d].append({"p0": ps[0], "per": f"第 {services.period_label(ps)} 節",
                              "time": services.time_range(ps), "course": c})
    day = request.GET.get("day", "1")
    day = int(day) if day.isdigit() and 1 <= int(day) <= 7 else 1
    return render(request, "courses/schedule.html", {
        "blocks": blocks, "periods": [(i + 1, a, b) for i, (a, b) in enumerate(PERIODS)],
        "days": list(enumerate(DAYS, 1)), "day": day,
        "day_list": sorted(by_day[day], key=lambda x: x["p0"]), "credits": services.total_credits(courses),
        "cells": [(r, c) for r in range(2, 12) for c in range(2, 9)],
    })


@student_required
def schedule_ics(request):
    start = date(2026, 9, 14)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Course//TW"]
    for c in services.enrolled_courses(me(request)):
        for d, ps in c.day_periods():
            day = (start + timedelta(days=d - 1)).strftime("%Y%m%d")
            a = PERIODS[ps[0] - 1][0].replace(":", "")
            b = PERIODS[ps[-1] - 1][1].replace(":", "")
            lines += [
                "BEGIN:VEVENT", f"UID:{c.code}-{d}@course", f"SUMMARY:{c.name}", f"LOCATION:{c.place}",
                f"DESCRIPTION:{c.code} {c.teacher}", f"DTSTART;TZID=Asia/Taipei:{day}T{a}00",
                f"DTEND;TZID=Asia/Taipei:{day}T{b}00", "RRULE:FREQ=WEEKLY;COUNT=18", "END:VEVENT",
            ]
    lines.append("END:VCALENDAR")
    resp = HttpResponse("\r\n".join(lines), content_type="text/calendar; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="schedule.ics"'
    return resp


@student_required
def enrolled_list(request):
    student, setting = me(request), Setting.get()
    courses = services.enrolled_courses(student)
    credits = services.total_credits(courses)
    if credits < setting.min_credits:
        status, ok = f"未達最低 {setting.min_credits} 學分", False
    elif credits > setting.max_credits:
        status, ok = "超過上限", False
    else:
        status, ok = "符合學分規定", True
    enrolled_codes, wish_codes, reg_codes = student_state(student)
    wish = [course_card(w.course, student, enrolled_codes, wish_codes, reg_codes, setting.phase)
            for w in student.wishes.select_related("course")]
    return render(request, "courses/list.html", {
        "courses": courses, "credits": credits, "status": status, "credit_ok": ok,
        "wish": wish, "regs": [r.course for r in student.registrations.select_related("course")],
        "requests": student.add_requests.select_related("course"),
    })


@student_required
def grad(request):
    student = me(request)
    rows, earned, prog, missing = services.graduation(student)
    mine = {c.code for c in services.enrolled_courses(student)}
    required = [("CS101", "程式設計（一）"), ("CS102", "程式設計（二）"), ("CS201", "資料結構"), ("CS202", "離散數學"),
                ("MA201", "線性代數"), ("CS301", "演算法"), ("CS302", "作業系統"), ("CS390", "專題研究（一）")]
    req_rows = [
        {"name": f"{code} {name}",
         "status": "已修畢" if code in student.completed else "修習中" if code in mine else "未修"}
        for code, name in required
    ]
    return render(request, "courses/grad.html", {
        "rows": rows, "earned": earned, "prog": prog, "missing": missing,
        "total": services.GRAD_TOTAL, "req_rows": req_rows,
    })


@student_required
def history(request):
    return render(request, "courses/history.html", {"logs": me(request).history.all()})


# ---- 教師:只能管理自己授課的課程 ----

@role_required("teacher")
def teacher(request):
    mine = Course.objects.filter(teacher_user=request.user)
    course = None
    if mine.exists():
        course = get_object_or_404(mine, code=request.GET.get("course") or mine.first().code)
    return render(request, "courses/teacher.html", {
        "my_courses": mine, "c": course, "reqs": course.requests.all() if course else [],
        "next": request.get_full_path(),
    })


@require_POST
@role_required("teacher")
def teacher_issue(request):
    reqs = AddRequest.objects.filter(pk__in=request.POST.getlist("rid"), course__teacher_user=request.user)
    n = services.issue_codes(reqs)
    if n:
        messages.success(request, f"已核發 {n} 組授權碼")
    else:
        messages.error(request, "請先勾選待審核的申請")
    return back(request, "courses:teacher")


@require_POST
@role_required("teacher")
def teacher_reject(request, pk):
    updated = AddRequest.objects.filter(pk=pk, status="pending", course__teacher_user=request.user).update(status="rejected")
    (messages.success if updated else messages.error)(request, "已婉拒申請" if updated else "找不到可婉拒的申請")
    return back(request, "courses:teacher")


# ---- 教務處 ----

@role_required("admin")
def admin_courses(request):
    return render(request, "courses/admin_courses.html", {"courses": Course.objects.all()})


@require_POST
@role_required("admin")
def admin_course_update(request, code):
    course = get_object_or_404(Course, code=code)
    if "toggle" in request.POST:
        course.is_open = not course.is_open
        course.save(update_fields=["is_open"])
        messages.success(request, f"「{course.name}」已{'開課' if course.is_open else '停開'}")
    elif "capacity" in request.POST:
        try:
            cap = int(request.POST["capacity"])
        except ValueError:
            cap = 0
        if cap < course.enrolled_count:
            messages.error(request, f"人數上限不得低於目前選課人數（{course.enrolled_count}）")
        else:
            course.capacity = cap
            course.save(update_fields=["capacity"])
            messages.success(request, f"「{course.name}」人數上限改為 {cap}")
    return redirect("courses:admin_courses")


@role_required("admin")
def rules(request):
    setting = Setting.get()
    if request.method == "POST":
        if "rule" in request.POST:
            rule = get_object_or_404(Rule, pk=request.POST["rule"])
            rule.on = not rule.on
            rule.save(update_fields=["on"])
        else:
            try:
                lo, hi = int(request.POST["min_credits"]), int(request.POST["max_credits"])
            except (KeyError, ValueError):
                lo = hi = 0
            if 0 < lo <= hi:
                setting.min_credits, setting.max_credits = lo, hi
                setting.save(update_fields=["min_credits", "max_credits"])
                messages.success(request, "學分上下限已更新")
            else:
                messages.error(request, "學分設定不正確(最低需大於 0 且不大於上限)")
        return redirect("courses:rules")
    return render(request, "courses/rules.html", {
        "rules": Rule.objects.all(), "phases": Setting.PHASES, "next": request.get_full_path(),
    })


# ---- 系統 ----

@role_required("system")
def system(request):
    series = [random.randint(1800, 4200) for _ in range(40)]
    top = max(series)
    return render(request, "courses/system.html", {
        "online": random.randint(3300, 3700), "queue": random.randint(900, 1500),
        "hit": round(random.uniform(96.5, 98.5), 1),
        "bars": [round(v / top * 100) for v in series],
        "nodes": [(n, random.randint(30, 80)) for n in ["api-01", "api-02", "api-03", "api-04", "redis-01", "db-main"]],
    })
