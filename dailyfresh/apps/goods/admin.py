from django.contrib import admin
from celery_tasks.tasks import index_cache_static_html
from apps.goods.models import *
# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''新增或更新表中的数据时调用'''
        super().save_model(request, obj, form, change)
        # 发出任务，让celery worker重新生成首页静态页
        from celery_tasks.tasks import index_cache_static_html
        index_cache_static_html.delay()
    def delete_model(self, request, obj):
        '''删除表中的数据时调用'''
        super().delete_model(request, obj)
        # 发出任务，让celery worker重新生成首页静态页
        from celery_tasks.tasks import index_cache_static_html
        index_cache_static_html.delay()


admin.site.register(GoodsType, BaseModelAdmin)
admin.site.register(IndexGoodsBanner, BaseModelAdmin)
admin.site.register(IndexTypeGoodsBanner, BaseModelAdmin)
admin.site.register(IndexPromotionBanner, BaseModelAdmin)
































