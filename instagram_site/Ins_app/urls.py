from django.urls import path
from Ins_app import views

urlpatterns = [
    # path('',views.IDView.as_view(),name='ID'),
    path('',views.IndexView.as_view(),name='index'),
    path('hashtag/',views.HashtagView.as_view(),name='hashtag'),
    path('account/',views.AccountView.as_view(),name='account'),
]
