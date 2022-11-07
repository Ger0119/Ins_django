from django import forms

class IDForm(forms.Form):
    ID = forms.CharField(max_length=100,label='ID')

class HashtagForm(forms.Form):
    hashtag = forms.CharField(max_length=100,label='Hash Tag')

ACCOUNT_CHOICES = {
    0:'すべてのアカウント',
    1:'最近のアカウント',
}

class AccountForm(forms.Form):
    keyword = forms.CharField(max_length=100,label='Keyword')
    post_count = forms.IntegerField(label='Post Count')
    followers_count = forms.IntegerField(label='Followers Count')
    created_at = forms.ChoiceField(label='Created At',widget=forms.Select,choices=list(ACCOUNT_CHOICES.items()))
    year = forms.IntegerField(label='xx years before')