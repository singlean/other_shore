import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE","dailyfresh.settings")
# django.setup()

from celery import Celery
from dailyfresh import settings
from django.core.mail import send_mail
from django.template import loader,RequestContext
from django_redis import get_redis_connection
from apps.goods.models import *


app = Celery('celery_tasks.tasks', broker='redis://192.168.110.129:6379/8')

@app.task
def send_register_active_email(username, to_email,token):

    # 发送邮件
    title = "天天生鲜"
    massage = ""
    html_mess = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://%s/user/active/%s">http://%s/user/active/%s</a>' % (
    username, settings.SERVER_IP_PORT,token, settings.SERVER_IP_PORT,token)
    # 邮件标题,正文内容,发件人,收件人列表,html内容
    send_mail(title, massage, settings.EMAIL_FROM, [to_email], html_message=html_mess)


@app.task
def index_cache_static_html():

    # 商品种内显示
    goods_type = GoodsType.objects.all()
    # 首页轮播图
    index_goods_banner = IndexGoodsBanner.objects.all().order_by("index")
    # 促销活动
    index_pro_motion = IndexPromotionBanner.objects.all().order_by("index")

    # 首页商品展示信息
    for goods in goods_type:
        # 文字信息
        title_banner = IndexTypeGoodsBanner.objects.filter(display_type=0, type=goods)
        # 图片信息
        image_banner = IndexTypeGoodsBanner.objects.filter(display_type=1, type=goods)
        # 为商品种内动态的添加属性
        goods.title_banner = title_banner
        goods.image_banner = image_banner

    content = {"goods_type": goods_type,
               "index_goods_banner": index_goods_banner,
               "index_pro_motion": index_pro_motion}

    temp = loader.get_template("index_cache.html")

    static_index_html = temp.render(content)

    save_path = os.path.join(settings.BASE_DIR, "static/index.html")

    with open(save_path,"w") as f:
        f.write(static_index_html)




























