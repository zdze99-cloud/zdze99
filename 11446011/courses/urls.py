from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("phase/", views.switch_phase, name="phase"),
    # 學生
    path("search/", views.search, name="search"),
    path("course/<str:code>/", views.course_detail, name="detail"),
    path("course/<str:code>/act/", views.course_act, name="act"),
    path("course/<str:code>/drop/", views.course_drop, name="drop"),
    path("course/<str:code>/star/", views.course_star, name="star"),
    path("course/<str:code>/code/", views.course_use_code, name="use-code"),
    path("course/<str:code>/request/", views.course_request, name="request"),
    path("lottery/", views.lottery, name="lottery"),
    path("schedule/", views.schedule, name="schedule"),
    path("schedule.ics", views.schedule_ics, name="schedule-ics"),
    path("list/", views.enrolled_list, name="list"),
    path("grad/", views.grad, name="grad"),
    path("history/", views.history, name="history"),
    # 教師
    path("teacher/", views.teacher, name="teacher"),
    path("teacher/issue/", views.teacher_issue, name="teacher-issue"),
    path("teacher/reject/<int:pk>/", views.teacher_reject, name="teacher-reject"),
    # 教務處
    path("admin-courses/", views.admin_courses, name="admin_courses"),
    path("admin-courses/<str:code>/", views.admin_course_update, name="admin-course-update"),
    path("rules/", views.rules, name="rules"),
    # 系統
    path("system/", views.system, name="system"),
]
