from django.urls import path,re_path
from cart.views import CartAddView,CartInfoView,UpdateCartView,CartDeleteView,TestView,TestIndexView,Demo

urlpatterns = [
    re_path(r'^add$',CartAddView.as_view(),name='add'),#购物车添加
    re_path(r'cart$',CartInfoView.as_view(),name='show'),#购物车页面显示
    re_path(r'update$',UpdateCartView.as_view(),name='update'),#更新购物车
    path('delete',CartDeleteView.as_view(),name='delete'),#删除购物车中的商品
    path('test',TestIndexView.as_view(),name='test'),#测试的，无用
    path('del',Demo.as_view(),name='del'),#测试的，无用

]