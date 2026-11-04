from django.conf import settings
from django.db import models


class Setting(models.Model):
    """全站選課設定(只有一筆)。"""

    PHASES = [(1, "第一階段 · 登記分發"), (2, "第二階段 · 加退選"), (3, "特殊加選 · 授權碼")]

    phase = models.PositiveSmallIntegerField("目前階段", choices=PHASES, default=2)
    min_credits = models.PositiveSmallIntegerField("最低學分", default=16)
    max_credits = models.PositiveSmallIntegerField("學分上限", default=25)
    idle_minutes = models.PositiveSmallIntegerField("閒置登出(分)", default=20)

    class Meta:
        verbose_name = verbose_name_plural = "選課設定"

    def __str__(self):
        return f"選課設定(階段 {self.phase})"

    @classmethod
    def get(cls):
        return cls.objects.get_or_create(pk=1)[0]


class Rule(models.Model):
    """第一階段分發的優先權重規則。"""

    key = models.CharField("規則", max_length=40, unique=True)
    description = models.CharField("說明", max_length=120)
    on = models.BooleanField("啟用", default=False)

    class Meta:
        verbose_name = verbose_name_plural = "分發規則"

    def __str__(self):
        return self.key


class Course(models.Model):
    TYPES = [("必修", "必修"), ("選修", "選修"), ("通識", "通識"), ("體育", "體育")]

    code = models.CharField("課號", max_length=12, unique=True)
    name = models.CharField("課名", max_length=60)
    dept = models.CharField("開課系所", max_length=30)
    year = models.PositiveSmallIntegerField("適用年級(0=不限)", default=0)
    type = models.CharField("類別", max_length=4, choices=TYPES)
    area = models.CharField("通識領域", max_length=8, blank=True)
    teacher = models.CharField("授課教師", max_length=30)
    teacher_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="taught_courses", verbose_name="授課教師帳號",
    )
    credits = models.PositiveSmallIntegerField("學分")
    # [[星期, [節次, ...]], ...],例如 [[2, [3, 4]], [4, [3]]]
    slots = models.JSONField("上課時段", default=list)
    building = models.CharField("大樓", max_length=20)
    room = models.CharField("教室", max_length=10)
    capacity = models.PositiveIntegerField("人數上限")
    enrolled_count = models.PositiveIntegerField("目前人數", default=0)
    prereq = models.CharField("先修課號", max_length=12, blank=True)
    needs_code = models.BooleanField("需授權碼", default=False)
    is_open = models.BooleanField("開課中", default=True)
    description = models.TextField("課程簡介", blank=True)
    topics = models.JSONField("課程綱要", default=list, blank=True)
    book = models.CharField("教科書", max_length=120, blank=True)

    class Meta:
        ordering = ["code"]
        verbose_name = verbose_name_plural = "課程"

    def __str__(self):
        return f"{self.code} {self.name}"

    @property
    def is_full(self):
        return self.enrolled_count >= self.capacity

    @property
    def seats_left(self):
        return max(0, self.capacity - self.enrolled_count)

    @property
    def percent(self):
        return min(100, round(self.enrolled_count / self.capacity * 100)) if self.capacity else 0

    @property
    def place(self):
        return f"{self.building} {self.room}"

    def day_periods(self):
        return [(int(d), [int(p) for p in ps]) for d, ps in self.slots]

    def overlaps(self, other):
        return any(
            d == d2 and set(ps) & set(ps2)
            for d, ps in self.day_periods()
            for d2, ps2 in other.day_periods()
        )


class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
        related_name="student", verbose_name="登入帳號",
    )
    sid = models.CharField("學號", max_length=12, unique=True)
    name = models.CharField("姓名", max_length=30)
    dept = models.CharField("系所", max_length=30)
    year = models.PositiveSmallIntegerField("年級")
    # 已修畢課程 {課號: 課名}
    completed = models.JSONField("已修畢課程", default=dict, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "學生"

    def __str__(self):
        return f"{self.sid} {self.name}"


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "course"], name="uniq_enrollment")]
        verbose_name = verbose_name_plural = "選課"

    def __str__(self):
        return f"{self.student.sid} → {self.course.code}"


class Wish(models.Model):
    """課程查詢頁的星號收藏。"""

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="wishes")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "course"], name="uniq_wish")]
        verbose_name = verbose_name_plural = "收藏"


class Registration(models.Model):
    """第一階段登記的志願序。"""

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="registrations")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created", "id"]
        constraints = [models.UniqueConstraint(fields=["student", "course"], name="uniq_registration")]
        verbose_name = verbose_name_plural = "志願登記"


class AddRequest(models.Model):
    STATUS = [("pending", "待審核"), ("approved", "已核發"), ("rejected", "已婉拒"), ("used", "已使用")]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="requests")
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name="add_requests")
    name = models.CharField("姓名", max_length=30)
    sid = models.CharField("學號", max_length=12)
    dept = models.CharField("系級", max_length=20)
    reason = models.CharField("理由", max_length=200)
    status = models.CharField("狀態", max_length=10, choices=STATUS, default="pending")
    code = models.CharField("授權碼", max_length=12, blank=True)

    class Meta:
        ordering = ["id"]
        constraints = [models.UniqueConstraint(fields=["course", "sid"], name="uniq_request")]
        verbose_name = verbose_name_plural = "加簽申請"

    def __str__(self):
        return f"{self.sid} → {self.course.code} ({self.status})"


class HistoryLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="history")
    at = models.CharField("時間", max_length=16)
    stage = models.CharField("階段", max_length=10)
    action = models.CharField("動作", max_length=10)
    course = models.CharField("課程", max_length=80)
    ok = models.BooleanField("成功", default=True)
    result = models.CharField("結果", max_length=40)
    seq = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-seq", "-id"]
        verbose_name = verbose_name_plural = "選課紀錄"
