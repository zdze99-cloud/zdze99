from django.contrib import admin

from . import models

admin.site.register(models.Setting)
admin.site.register(models.Rule)
admin.site.register(models.Student)
admin.site.register(models.Enrollment)
admin.site.register(models.AddRequest)
admin.site.register(models.HistoryLog)


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "dept", "type", "teacher", "credits", "enrolled_count", "capacity", "is_open")
    list_filter = ("type", "dept", "is_open")
    search_fields = ("code", "name", "teacher")
