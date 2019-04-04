from django.urls import path,re_path
from user import views
from user.views import RegisterView,ActiveView,LoginView

urlpatterns = [
    #path('login',views.login),#登录
    path('index',views.index,name='index'),#首页
    path('register',RegisterView.as_view(),name='register'),#注册
    re_path(r'active/(?P<token>.*)$',ActiveView.as_view(),name='active'),#激活
    path('login',LoginView.as_view(),name='login'),#登录
]