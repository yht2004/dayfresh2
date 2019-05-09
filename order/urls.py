from django.urls import path,re_path
from order.views import OrderPlaceView,OrderCommitView

urlpatterns = [
    re_path(r'place$',OrderPlaceView.as_view(),name='place'),
    re_path(r'commit$',OrderCommitView.as_view(),name='commit'),
]