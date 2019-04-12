from django.urls import path,re_path
from django.contrib.auth.decorators import login_required
from user import views
from user.views import RegisterView,ActiveView,LoginView,UserInfo,UserAddress,UserOrder,LogoutView


urlpatterns = [
    path('register',RegisterView.as_view(),name='register'),#注册
    re_path(r'active/(?P<token>.*)$',ActiveView.as_view(),name='active'),#激活
    path('login',LoginView.as_view(),name='login'),#登录
    path('logout',LoginView.as_view(),name='logout'),#退出

    # path('user',login_required(UserInfo.as_view()),name='user'),#用户中心页面
    # path('order',UserOrder.as_view(),name='order'),#用户订单页面
    # path('address',login_required(UserAddress.as_view()),name='address'),#用户地址页面

    path('user', UserInfo.as_view(), name='user'),  # 用户中心页面
    path('order', UserOrder.as_view(), name='order'),  # 用户订单页面
    path('address', UserAddress.as_view(), name='address'),  # 用户地址页面，非登陆用户不得访问的资源

]
