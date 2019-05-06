from django.urls import path,re_path
from cart.views import CartAddView

urlpatterns = [
    re_path(r'^add$',CartAddView.as_view(),name='add'),#购物车添加

]