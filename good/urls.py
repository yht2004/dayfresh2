from django.urls import path,re_path
from good.views import IndexView


urlpatterns = [

    path('index',IndexView.as_view(),name='index'),#首页

]