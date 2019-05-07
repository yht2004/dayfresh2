from django.urls import path,re_path
from good.views import IndexView,DetailView,ListView


urlpatterns = [

    re_path(r'index$',IndexView.as_view(),name='index'),#首页
    re_path(r'^good/(?P<goods_id>\d+)$',DetailView.as_view(),name='detail'),#商品详情页面
    re_path(r'^list/(?P<type_id>\d+)/(?P<page>\d+)$',ListView.as_view(),name='list'),#商品列表页

]