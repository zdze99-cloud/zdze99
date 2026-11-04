from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction

from courses import seed_data as d
from courses.context import ROLE_GROUPS
from courses.models import (
    AddRequest, Course, Enrollment, HistoryLog, Registration, Rule, Setting, Student, Wish,
)

DEMO_PASSWORD = "1234"

RULES = [
    ("本系生優先", "第一階段分發時本系學生權重 ×2", True),
    ("大四應屆畢業生優先", "必修課優先分發給應屆畢業生", True),
    ("延畢生優先", "延修生於第一階段保留 5% 名額", False),
    ("雙主修 / 輔系保留名額", "保留 10% 名額給雙主修與輔系學生", False),
]

# 教師姓名 → 登入帳號;林俊杰教 CS315、CS330,示範加簽流程用
TEACHER_ACCOUNTS = {
    "林俊杰": "lin", "李佳穎": "lee", "陳建宏": "chen", "王明哲": "wang", "張志豪": "chang", "周育德": "chou",
    "Emily Carter": "carter", "吳宛真": "wu", "鄭安琪": "cheng", "劉冠廷": "liu", "蔡明蓉": "tsai",
    "林志偉": "linzw", "許雅雯": "hsu", "黃俊傑": "huang", "楊淑芬": "yang", "何家豪": "ho",
}
TEACHER_ACCOUNTS.update(d.EXTRA_TEACHER_ACCOUNTS)
STAFF_ACCOUNTS = [("registrar", "王秀蘭", "admin"), ("sysadmin", "系統管理員", "system")]
DEPT_FULL = {"資工": "資訊工程學系", "電機": "電機工程學系", "應數": "應用數學系"}
YEAR_NUM = {"一": 1, "二": 2, "三": 3, "四": 4}


def make_user(username, full_name, group):
    user = User.objects.create_user(username=username, password=DEMO_PASSWORD, first_name=full_name)
    user.groups.add(group)
    return user


class Command(BaseCommand):
    help = "載入選課系統示範資料與帳號(會清空現有選課資料與示範帳號後重建,superuser 會保留)"

    @transaction.atomic
    def handle(self, *args, **options):
        for m in (HistoryLog, AddRequest, Registration, Wish, Enrollment, Course, Student, Rule):
            m.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        groups = {name: Group.objects.get_or_create(name=name)[0] for name in ROLE_GROUPS}

        Setting.objects.update_or_create(pk=1, defaults={"phase": 2})
        for key, desc, on in RULES:
            Rule.objects.create(key=key, description=desc, on=on)

        # 主角學生 + 加簽申請裡出現的其他學生,都建立帳號(帳號 = 學號)
        student = Student.objects.create(
            user=make_user(d.ME["sid"], d.ME["name"], groups["student"]), **d.ME, completed=d.DONE,
        )
        students = {student.sid: student}
        for r in d.REQUESTS:
            if r["sid"] in students:
                continue
            short, year = r["dept"][:-1], r["dept"][-1]
            students[r["sid"]] = Student.objects.create(
                user=make_user(r["sid"], r["name"], groups["student"]),
                sid=r["sid"], name=r["name"], dept=DEPT_FULL.get(short, short), year=YEAR_NUM.get(year, 1),
            )

        teachers = {name: make_user(acc, name, groups["teacher"]) for name, acc in TEACHER_ACCOUNTS.items()}
        for username, full, role in STAFF_ACCOUNTS:
            make_user(username, full, groups[role])

        by_code = {}
        for c in d.COURSES:
            by_code[c["id"]] = Course.objects.create(
                code=c["id"], name=c["name"], dept=c["dept"], year=c["year"], type=c["type"],
                area=c.get("area", ""), teacher=c["teacher"], teacher_user=teachers.get(c["teacher"]),
                credits=c["credits"], slots=c["slots"],
                building=c["bld"], room=c["room"], capacity=c["cap"], enrolled_count=c["enr"],
                prereq=c.get("pre", ""), needs_code=c.get("code", False),
                description=c.get("desc", ""), topics=c.get("topics", []), book=c.get("book", ""),
            )
        for code in ["CS301", "MA201", "GE105", "PE120", "CS330"]:
            Enrollment.objects.create(student=student, course=by_code[code])
        for code in ["CS320", "CS315", "GE318", "EN301"]:
            Wish.objects.create(student=student, course=by_code[code])
        for r in d.REQUESTS:
            AddRequest.objects.create(
                course=by_code[r["course"]], student=students[r["sid"]], name=r["name"], sid=r["sid"],
                dept=r["dept"], reason=r["reason"], status=r["status"], code=r.get("code", ""),
            )
        n = len(d.HISTORY)
        for i, h in enumerate(d.HISTORY):
            HistoryLog.objects.create(
                student=student, at=h["t"], stage=h["stage"], action=h["act"],
                course=h["course"], ok=h["ok"], result=h["res"], seq=n - i,
            )
        self.stdout.write(self.style.SUCCESS(
            f"已載入 {len(by_code)} 門課程、{len(students)} 位學生、{len(teachers)} 位教師。"
            f"所有示範帳號密碼皆為 {DEMO_PASSWORD}"
        ))
