from django import forms
from .models import Member
import re

class StaffEarnForm(forms.Form):
    barcode_token = forms.CharField(max_length=64)
    amount_twd = forms.DecimalField(min_value=0, decimal_places=0, max_digits=10)
    note = forms.CharField(required=False)

class MemberProfileForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ["display_name", "birthday", "phone"]
        widgets = {
            "display_name": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "請輸入姓名"
            }),
            "birthday": forms.DateInput(attrs={
                "class": "form-control", "type": "date"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control", "inputmode": "tel", "placeholder": "09xx-xxx-xxx"
            }),
        }
        labels = {
            "display_name": "姓名",
            "birthday": "生日",
            "phone": "電話",
        }

    def clean_phone(self):
        p = (self.cleaned_data.get("phone") or "").strip()
        if not p:
            return p
        # 你可以改成自己的格式需求
        if not re.match(r"^\d[\d\- ]{7,}$", p):
            raise forms.ValidationError("電話格式不正確")
        return p