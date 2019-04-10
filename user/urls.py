from django.urls import path,re_path
from user import views
from user.views import RegisterView,ActiveView,LoginView,UserInfo,UserAddress,UserOrder


urlpatterns = [
    path('register',RegisterView.as_view(),name='register'),#注册
    re_path(r'active/(?P<token>.*)$',ActiveView.as_view(),name='active'),#激活
    path('login',LoginView.as_view(),name='login'),#登录

    path('userinfo',UserInfo.as_view(),name='userinfo'),#用户中心页面
    path('userorder',UserOrder.as_view(),name='userorder'),#用户订单页面
    path('usersite',UserAddress.as_view(),name='usersite'),#用户地址页面


]