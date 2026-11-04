from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from . import services
from .models import AddRequest, Course, Setting, Student


class BaseCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        cls.student = Student.objects.get(sid="11446011")
        cls.other = Student.objects.get(sid="B11202045")

    def login(self, username="11446011"):
        self.client.force_login(User.objects.get(username=username))

    def set_phase(self, p):
        s = Setting.get()
        s.phase = p
        s.save()


class RuleTests(BaseCase):
    def test_seed_enrolled_credits(self):
        self.assertEqual(services.total_credits(services.enrolled_courses(self.student)), 12)

    def test_conflict_detected(self):
        # CS320(週二 3-4)與已選 CS301(週二 3-4)衝堂
        r = services.enroll(self.student, Course.objects.get(code="CS320"))
        self.assertFalse(r.ok)
        self.assertIn("衝堂", r.message)

    def test_full_course_rejected_in_phase2(self):
        self.assertFalse(services.enroll(self.student, Course.objects.get(code="CS302")).ok)

    def test_prereq_blocks(self):
        r = services.enroll(self.student, Course.objects.get(code="CS390"))
        self.assertFalse(r.ok)
        self.assertIn("先修", r.message)

    def test_enroll_and_drop_updates_count(self):
        c = Course.objects.get(code="EN301")
        before = c.enrolled_count
        self.assertTrue(services.enroll(self.student, c).ok)
        c.refresh_from_db()
        self.assertEqual(c.enrolled_count, before + 1)
        services.drop(self.student, c)
        c.refresh_from_db()
        self.assertEqual(c.enrolled_count, before)

    def test_authorization_code_flow(self):
        self.set_phase(3)
        c = Course.objects.get(code="CS315")
        req = AddRequest.objects.get(course=c, sid=self.student.sid)
        self.assertFalse(services.use_code(self.student, c, "WRONG").ok)
        services.issue_codes(AddRequest.objects.filter(pk=req.pk))
        req.refresh_from_db()
        self.assertEqual(req.status, "approved")
        self.assertTrue(services.use_code(self.student, c, req.code.lower()).ok)
        req.refresh_from_db()
        self.assertEqual(req.status, "used")


class AuthTests(BaseCase):
    def test_requires_login(self):
        res = self.client.get(reverse("courses:search"))
        self.assertRedirects(res, reverse("courses:login") + "?next=" + reverse("courses:search"))

    def test_login_with_password(self):
        res = self.client.post(reverse("courses:login"), {"username": "11446011", "password": "1234"})
        self.assertRedirects(res, reverse("courses:home"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("courses:search")).status_code, 200)

    def test_wrong_password(self):
        res = self.client.post(reverse("courses:login"), {"username": "11446011", "password": "nope"})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "帳號或密碼錯誤")

    def test_logout_requires_post(self):
        self.login()
        self.client.post(reverse("courses:logout"))
        self.assertEqual(self.client.get(reverse("courses:search")).status_code, 302)

    def test_home_redirects_by_role(self):
        for username, page in [("11446011", "search"), ("lin", "teacher"), ("registrar", "admin_courses"), ("sysadmin", "system")]:
            self.login(username)
            self.assertRedirects(self.client.get(reverse("courses:home")), reverse(f"courses:{page}"))

    def test_role_guard(self):
        self.login()
        res = self.client.get(reverse("courses:system"))
        self.assertRedirects(res, reverse("courses:home"), fetch_redirect_response=False)

    def test_student_cannot_switch_phase(self):
        self.login()
        self.client.post(reverse("courses:phase"), {"phase": 1})
        self.assertEqual(Setting.get().phase, 2)
        self.login("registrar")
        self.client.post(reverse("courses:phase"), {"phase": 1})
        self.assertEqual(Setting.get().phase, 1)

    def test_each_student_sees_own_data(self):
        self.login("B11202045")
        res = self.client.get(reverse("courses:list"))
        self.assertEqual(res.context["courses"], [])
        self.client.post(reverse("courses:act", args=["EN301"]))
        self.assertTrue(self.other.enrollments.filter(course__code="EN301").exists())
        self.assertFalse(self.student.enrollments.filter(course__code="EN301").exists())


class PageTests(BaseCase):
    def test_all_pages_render(self):
        self.login()
        for name in ["search", "schedule", "list", "grad", "history"]:
            self.assertEqual(self.client.get(reverse(f"courses:{name}")).status_code, 200, name)
        self.assertEqual(self.client.get(reverse("courses:detail", args=["CS315"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("courses:schedule-ics")).status_code, 200)
        for username, name in [("lin", "teacher"), ("registrar", "admin_courses"), ("registrar", "rules"), ("sysadmin", "system")]:
            self.login(username)
            self.assertEqual(self.client.get(reverse(f"courses:{name}")).status_code, 200, name)

    def test_search_filter(self):
        self.login()
        res = self.client.get(reverse("courses:search"), {"q": "演算法"})
        self.assertEqual([c.code for c in res.context["cards"]], ["CS301"])

    def test_open_redirect_blocked(self):
        self.login()
        res = self.client.post(reverse("courses:star", args=["EN301"]), {"next": "https://evil.example/"})
        self.assertRedirects(res, reverse("courses:search"))

    def test_lottery(self):
        self.set_phase(1)
        self.login()
        self.client.post(reverse("courses:act", args=["EN301"]))
        self.assertEqual(self.student.registrations.count(), 1)
        self.client.post(reverse("courses:lottery"))
        self.assertEqual(self.student.registrations.count(), 0)


class AddRequestTests(BaseCase):
    url = staticmethod(lambda code: reverse("courses:request", args=[code]))

    def test_student_submits_request(self):
        # CS302 已額滿、萬睿鈞尚未申請
        self.login()
        res = self.client.post(self.url("CS302"), {"reason": "應屆畢業,作業系統是必修,請老師幫忙加簽。"})
        self.assertRedirects(res, reverse("courses:detail", args=["CS302"]))
        req = AddRequest.objects.get(course__code="CS302", sid="11446011")
        self.assertEqual((req.status, req.student), ("pending", self.student))
        self.assertEqual(self.student.history.first().action, "申請加簽")

    def test_reason_too_short(self):
        self.login()
        res = self.client.post(self.url("CS302"), {"reason": "拜託"})
        self.assertEqual(res.status_code, 400)
        self.assertContains(res, "至少用 10 個字", status_code=400)
        self.assertFalse(AddRequest.objects.filter(course__code="CS302", sid="11446011").exists())

    def test_duplicate_request_blocked(self):
        # 萬睿鈞已申請過 CS315
        self.login()
        self.client.post(self.url("CS315"), {"reason": "再申請一次看看會不會重複建立。"})
        self.assertEqual(AddRequest.objects.filter(course__code="CS315", sid="11446011").count(), 1)

    def test_open_course_needs_no_request(self):
        # EN301 尚有名額、不需授權碼
        self.login()
        self.client.post(self.url("EN301"), {"reason": "這門課還有名額,應該不能申請。"})
        self.assertFalse(AddRequest.objects.filter(course__code="EN301").exists())

    def test_teacher_sees_and_approves_new_request(self):
        # 陳柏宇在 CS315 有一筆待審申請,由授課的林俊杰核發
        req = AddRequest.objects.get(course__code="CS315", sid="B11202045")
        self.login("lin")
        res = self.client.get(reverse("courses:teacher") + "?course=CS315")
        self.assertIn(req, list(res.context["reqs"]))
        self.client.post(reverse("courses:teacher-issue"), {"rid": [req.pk]})
        req.refresh_from_db()
        self.assertEqual(req.status, "approved")
        self.assertTrue(req.code)

    def test_teacher_cannot_touch_other_teachers_requests(self):
        # CS302 由王明哲授課;林俊杰不能核發或婉拒
        self.login()
        self.client.post(self.url("CS302"), {"reason": "應屆畢業,作業系統是必修,請老師幫忙加簽。"})
        req = AddRequest.objects.get(course__code="CS302", sid="11446011")
        self.login("lin")
        self.client.post(reverse("courses:teacher-issue"), {"rid": [req.pk]})
        self.client.post(reverse("courses:teacher-reject", args=[req.pk]))
        req.refresh_from_db()
        self.assertEqual(req.status, "pending")
        self.assertEqual(self.client.get(reverse("courses:teacher") + "?course=CS302").status_code, 404)
        self.login("wang")
        self.client.post(reverse("courses:teacher-issue"), {"rid": [req.pk]})
        req.refresh_from_db()
        self.assertEqual(req.status, "approved")
