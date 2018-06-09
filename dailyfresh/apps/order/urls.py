from django.conf.urls import url
from apps.order.views import *


urlpatterns = [
    url(r"^place$", PlaceView.as_view(), name="place"),  # 订单提交界面
    url(r"^commit$", CommitView.as_view(), name="commit"),  # 创建订单视图
]
