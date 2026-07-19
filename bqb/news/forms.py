from django import forms
from .models import News, Cities, Counties, Region


# CITY_CHOICES = [
#     ('Taos', 'Taos'),
#     ('Torrance', 'Torrance'),
#     ('Union', 'Union'),
#     ('Valencia', 'Valencia')]
#

class NewsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    class Meta:
        model = News
        fields = ("__all__")



    #     # fields = ['source',
    #     #           'title',
    #     #           'city',
    #     #           'county',
    #     #           'region',
    #     #           'published']
    #
    # source = forms.CharField()
    # title = forms.CharField()
    # city = forms.ChoiceField(choices=[
    #     (choice, choice) for choice in Cities.objects.all()])
    # county = forms.ChoiceField(choices=[
    #     (choice, choice) for choice in Counties.objects.all()])
    # region = forms.ChoiceField(choices=[
    #     (choice, choice) for choice in Region.objects.all()])
    # city = forms.ChoiceField(choices=CITY_CHOICES)
    # county = forms.CharField()
    # region = forms.CharField()
    # published = forms.DateField()
