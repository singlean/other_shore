from django.conf.urls import url
from apps.cart.views import *

urlpatterns = [
    url(r"^add$", CartAddView.as_view(), name="add"),  # 添加购物车记录
    url(r"^info$", CartInfoView.as_view(), name="info"),  # 购物车显示界面
]
