from django import forms

from .models import AddRequest


class AddRequestForm(forms.ModelForm):
    """學生向授課教師申請加簽。"""

    class Meta:
        model = AddRequest
        fields = ["reason"]
        labels = {"reason": "申請理由"}
        widgets = {
            "reason": forms.Textarea(attrs={
                "class": "input", "rows": 3, "maxlength": 200,
                "placeholder": "例如:專題方向需要、應屆畢業、已修畢相關先修課…",
            }),
        }

    def clean_reason(self):
        reason = self.cleaned_data["reason"].strip()
        if len(reason) < 10:
            raise forms.ValidationError("請至少用 10 個字說明申請理由。")
        return reason
