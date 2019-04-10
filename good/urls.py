from django.urls import path,re_path
from good import views


urlpatterns = [

    path('index',views.index,name='index'),#首页

]