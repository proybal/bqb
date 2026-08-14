from django import forms
from .models import News, Cities, Counties, Region


class NewsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    class Meta:
        model = News
        fields = ("__all__")



