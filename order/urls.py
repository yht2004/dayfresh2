from django.urls import path,re_path
from order.views import OrderPlaceView,OrderCommitView,OrderPayView,CheckPayView,CommentView

urlpatterns = [
    re_path(r'place$',OrderPlaceView.as_view(),name='place'),
    re_path(r'commit$',OrderCommitView.as_view(),name='commit'),
    re_path(r'pay$',OrderPayView.as_view(),name='pay'),#支付
    re_path(r'check',CheckPayView.as_view(),name='check'),#查询支付交易结果
    re_path(r'comment/(?P<order_id>.+)$',CommentView.as_view(),name='comment'),#订单评论
]