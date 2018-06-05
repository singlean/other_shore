from django.conf.urls import url
from apps.goods.views import *

urlpatterns = [
    url(r"^$", IndexView.as_view(), name="index"), # 主页
    url(r"^detail/(\d+)$",Detailview.as_view(), name="detail"), # 商品详情页
    url(r"^list/(?P<type_id>\d+)/(?P<page_num>\d*)$",Listview.as_view(), name="list"),  # 商品列表页
]


