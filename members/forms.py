from django import forms

class StaffEarnForm(forms.Form):
    barcode_token = forms.CharField(max_length=64)
    amount_twd = forms.DecimalField(min_value=0, decimal_places=0, max_digits=10)
    note = forms.CharField(required=False)
