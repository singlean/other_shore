from django.conf.urls import url
from apps.cart.views import *

urlpatterns = [
    url(r"^add$", CartAddView.as_view(), name="add"),  # 添加购物车记录
    url(r"^info$", CartInfoView.as_view(), name="info"),  # 购物车显示界面
    url(r"^update$", CartUpdateView.as_view(),name="update"),  # 购物车商品修改视图
    url(r"^delete$",CartDeleteView.as_view(), name="delete"),  # 商品删除视图
]
