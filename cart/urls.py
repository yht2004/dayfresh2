from django.urls import path,re_path
from cart.views import CartAddView,CartInfoView,UpdateCartView,CartDeleteView

urlpatterns = [
    re_path(r'^add$',CartAddView.as_view(),name='add'),#购物车添加
    re_path(r'$',CartInfoView.as_view(),name='show'),#购物车页面显示
    re_path(r'update$',UpdateCartView.as_view(),name='update'),#更新购物车
    re_path(r'del',CartDeleteView.as_view(),name='del'),#更新购物车
]