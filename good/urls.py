from django.urls import path,re_path
from good.views import IndexView,DetailView


urlpatterns = [

    path('index',IndexView.as_view(),name='index'),#首页
    re_path(r'^good/(?P<goods_id>\d+)$',DetailView.as_view(),name='detail'),#商品详情页面


]