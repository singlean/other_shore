from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from apps.goods.models import *
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin

# Create your views here.


class CartAddView(View):

    def post(self,request):

        # 登陆验证
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({"res": 0, "error": "未登录"})

        # 接受参数
        sku_id = request.POST.get("sku_id")
        count = request.POST.get("count")

        # 校验函数
        if not all([sku_id,count]):
            return JsonResponse({"res":1,"error":"数据不完整"})
        # 判断是否为有效商品
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except:
            return JsonResponse({"res":2,"error":"商品无"})

        try:
            count = int(count)
        except:
            return JsonResponse({"res":3,"error":"数量错误"})

        # 业务处理
        conn = get_redis_connection("default")
        cart_key = "cart_%d"%user.id
        # 获取redis中次商品的数量,如果没有则为None
        cart_count = conn.hget(cart_key,sku_id)
        if cart_count:
            count += int(cart_count)
        # 判断库存是否充足
        if count > sku.stock:
            return JsonResponse({"res": 4, "error": "库存不足"})

        # 如果有此条数据,则修改,没有就添加
        conn.hset(cart_key,sku_id,count)
        # 查询商品数,返回结果
        redis_count = conn.hlen(cart_key)
        print(redis_count)
        return JsonResponse({"res": 5, "success": "添加成功","redis_count":redis_count})


class CartInfoView(LoginRequiredMixin,View):

    def get(self,request):

        # 获取用户
        user = request.user
        # 连接redis
        conn = get_redis_connection("default")
        cart_key = "cart_%d"%user.id
        cart_sku = conn.hgetall(cart_key)
        # 商品数量　单个商品数量小计　单个商品价格小计　总价　商品对象
        sku_count = 0
        price_count = 0
        skus = []
        for k,v in cart_sku.items():
            sku = GoodsSKU.objects.get(id=k)
            # 总数量
            sku_count += int(v)
            c_price = sku.price * int(v)
            # 总价格
            price_count += c_price
            # 动态添加数量小计和价格小计
            sku.sku_count = v
            sku.sku_price = c_price
            # 添加商品对象
            skus.append(sku)

        context = {"sku_count":sku_count,"price_count":price_count,"skus":skus}

        return render(request,"cart_info.html",context)


class CartUpdateView(View):

    def post(self,request):

        # 登陆验证
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({"res": 0, "error": "未登录"})

        # 接受参数
        sku_id = request.POST.get("sku_id")
        sku_count = request.POST.get("sku_count")

        # 校验函数
        if not all([sku_id,sku_id]):
            return JsonResponse({"res":1,"error":"数据不完整"})
        # 判断是否为有效商品
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except:
            return JsonResponse({"res":2,"error":"商品无"})
        # 判断数量是否为空或其他
        try:
            sku_count = int(sku_count)
        except:
            return JsonResponse({"res":3,"error":"数量错误"})

        # 业务处理
        conn = get_redis_connection("default")
        cart_key = "cart_%d"%user.id
        # 判断库存是否充足
        if sku_count > sku.stock:
            user_sku_count = int(conn.hget(cart_key,sku_id))
            return JsonResponse({"res": 4, "error": "库存不足","user_sku_count":user_sku_count})

        # 修改次商品的数量
        conn.hset(cart_key,sku_id,sku_count)
        # 查询商品数,返回结果
        redis_count = conn.hlen(cart_key)
        return JsonResponse({"res": 5, "success": "添加成功","redis_count":redis_count})


class CartDeleteView(View):

    def post(self,request):

        # 登陆验证
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({"res": 0, "error": "未登录"})
        # 接受参数
        sku_id = request.POST.get("sku_id")
        # 判断数据是否为空
        if not sku_id:
            return JsonResponse({"res":1,"error":"数据为空"})
        # 判断是否有此商品
        sku = GoodsSKU.objects.filter(id=sku_id)
        if not sku:
            return JsonResponse({"res": 2, "error": "没有此商品"})

        cart_key = "cart_%d"%user.id
        conn = get_redis_connection("default")
        conn.hdel(cart_key,sku_id)

        return JsonResponse({"res":3,"ok":"删除成功"})


























