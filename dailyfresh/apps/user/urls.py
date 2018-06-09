from django.conf.urls import url
from apps.user.views import *

urlpatterns = [
    url(r"^register$",RegisterView.as_view(),name="register"),  # 注册
    url(r"^active/(?P<token>.*)$", ActiveView.as_view(),name="active"),  # 激活
    url(r"^login$", LoginView.as_view(), name="login"),  # 登陆界面
    url(r"^logout$", Logoutview.as_view(), name="logout"),  # 退出登陆

    url(r"^user$", Userinfoview.as_view(), name="user"),     # 用户中心
    url(r"^order/(\d+)$", Userorderview.as_view(), name="order"),  # 订单页
    url(r"^address$", Addressview.as_view(), name="address"),  #　添加信息



]













