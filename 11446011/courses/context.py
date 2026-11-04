from .models import Setting

NAV = {
    "student": [("search", "課程查詢"), ("schedule", "我的課表"), ("list", "選課清單"), ("grad", "畢業檢核"), ("history", "選課紀錄")],
    "teacher": [("teacher", "加簽管理")],
    "admin": [("admin_courses", "開課管理"), ("rules", "選課設定")],
    "system": [("system", "系統監控")],
}
ROLE_LABELS = {"student": "學生", "teacher": "教師", "admin": "教務處", "system": "系統"}
# Django Group 名稱 → 角色;一個帳號只屬於一個角色
ROLE_GROUPS = ["student", "teacher", "admin", "system"]


def role_of(user):
    """依帳號所屬的 Group 決定角色;superuser 視為教務處。"""
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return "admin"
    names = set(user.groups.values_list("name", flat=True))
    return next((r for r in ROLE_GROUPS if r in names), None)


def display_of(user, role):
    full = user.get_full_name() or user.username
    if role == "student" and hasattr(user, "student"):
        s = user.student
        return s.name, f"{s.dept} {s.year} 年級 · {s.sid}"
    if role == "teacher":
        return full, "授課教師"
    if role == "admin":
        return "教務處 註冊組", full
    return full, ROLE_LABELS.get(role, "")


def shell(request):
    """每個頁面共用的 context:角色、導覽列、目前階段。"""
    setting = Setting.get()
    role = role_of(request.user)
    name, sub = display_of(request.user, role) if role else ("", "")
    return {
        "role": role,
        "role_label": ROLE_LABELS.get(role, ""),
        "nav": NAV.get(role, []),
        "user_name": name,
        "user_sub": sub,
        "setting": setting,
        "phase_name": dict(Setting.PHASES)[setting.phase],
        "idle_minutes": setting.idle_minutes,
    }
