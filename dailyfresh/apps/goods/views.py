from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from apps.goods.models import *
from apps.order.models import *
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.paginator import Paginator


# Create your views here.


class IndexView(View):

    def get(self,request):

        # 获取缓存数据,返回结果是一个字典
        content = cache.get("index_page_data")
        if content is None:

            # 商品种内显示
            goods_type = GoodsType.objects.all()
            # 首页轮播图
            index_goods_banner = IndexGoodsBanner.objects.all().order_by("index")
            # 促销活动
            index_pro_motion = IndexPromotionBanner.objects.all().order_by("index")

            # 首页商品展示信息
            for goods in goods_type:
                # 文字信息
                title_banner = IndexTypeGoodsBanner.objects.filter(display_type=0,type=goods)
                # 图片信息
                image_banner = IndexTypeGoodsBanner.objects.filter(display_type=1,type=goods)
                # 为商品种内动态的添加属性
                goods.title_banner = title_banner
                goods.image_banner = image_banner

            content = {"goods_type":goods_type,
                       "index_goods_banner":index_goods_banner,
                       "index_pro_motion":index_pro_motion}

            # 将首页相同数据设置缓存
            # cache.set("index_page_data",content,600)

        # 获取购物车商品记录
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            conn = get_redis_connection("default")
            cart_key = "cart_%d"%user.id
            cart_count = conn.hlen(cart_key)

        # 想字典中添加购物车记录
        content.update(cart_count=cart_count)

        # 使用模板
        return render(request,"index.html",content)


class Detailview(View):

    def get(self,request,sku_id):
        # 有商品显示,没有跳转到首页
        try:
            details = GoodsSKU.objects.get(id=sku_id)
        except:
            return redirect(reverse("goods:index"))

        # 获取商品分类信息
        types = GoodsType.objects.all()
        # 获取商品的评论信息
        sku_orders = OrderGoods.objects.filter(sku=details).exclude(comment='')
        # 获取新品信息
        new_sku = GoodsSKU.objects.filter(type=details.type).order_by('-create_time')[:2]
        # 获取同一个SPU的其他规格商品
        same_spu = GoodsSKU.objects.filter(goods=details.goods).exclude(id=details.id)

        # 获取购物车记录
        cart_count = 0
        user = request.user
        if user.is_authenticated():
            cart_key = "cart_%d"%user.id
            conn = get_redis_connection("default")
            cart_count = conn.hlen(cart_key)

            history_key = "history_%d"%user.id
            # 删除此记录在数据库中的信息,没有这个数据不执行
            conn.lrem(history_key,0,sku_id)
            # 添加数据
            conn.lpush(history_key,sku_id)
            # 只保留五条
            conn.ltrim(history_key,0,4)

        context = {"cart_count":cart_count,"details":details,"new_sku":new_sku,
                   "same_spu":same_spu,"types":types,
                   "sku_orders":sku_orders}

        return render(request,"detail.html",context)


class Listview(View):

    def get(self,request,type_id,page_num):
        # 若没有此种商品分类,则跳转到首页
        try:
            now_type = GoodsType.objects.get(id=type_id)
        except:
            return redirect(reverse("goods:index"))
        # 获取所有商品种类
        types = GoodsType.objects.all()
        # 获取新品信息
        new_sku = GoodsSKU.objects.filter(type=now_type.id).order_by('-create_time')[:2]
        # 获取此类所有商品并判断排序方式
        sort = request.GET.get("sort")
        if sort == "pri":
            goods_skus = GoodsSKU.objects.filter(type=type_id).order_by("price")
        elif sort == "hot":
            goods_skus = GoodsSKU.objects.filter(type=type_id).order_by("-sales")
        else:
            sort = "default"
            goods_skus = GoodsSKU.objects.filter(type=type_id).order_by("-id")
        # 分页显示
        paginator = Paginator(goods_skus,1)
        # 获取总页数
        pages = paginator.num_pages
        # 页码数为空或大于总页数,赋值为１
        if not page_num:
            page_num = 1
        elif pages < int(page_num):
            page_num = 1
        # 获取当前页数据
        page = paginator.page(page_num)
        # 总页数小于等于五,显示所有
        # 当前页小于等于３,显示1到5
        # 当前页为后三页,显示最后5页
        # 显示前后共5页
        # 获取页码列表
        if pages <=5:
            page_list = range(1,pages+1)
        elif int(page_num)<=3:
            page_list = range(1,6)
        elif int(page_num) > pages-3:
            page_list = range(pages-4,pages+1)
        else:
            page_list = range(page_num-2,page_num+3)
        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)
        # 模板上下文
        context = {"page":page,"now_type":now_type,
                   "types":types,"sort":sort,
                   "new_sku":new_sku,
                   "page_list":page_list,
                   "cart_count":cart_count}
        # 使用模板
        return render(request,"list.html",context)






































