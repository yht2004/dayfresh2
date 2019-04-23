from django.contrib import admin
from django.core.cache import cache
from good.models import GoodsType,IndexPromotionBanner,IndexGoodsBanner,IndexTypeGoodsBanner

# Register your models here.

class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        from celery_tasks.tasks import generate_static_index_html
        #generate_static_index_html.delay()

        #cache.delete('index_page_data')

    def delete_model(self, request, obj):
        super().delete_model(request,obj)
        from celery_tasks.tasks import generate_static_index_html
        #generate_static_index_html.delay()

        #cache.delete('index_page_data')

class GoodsTypeAdmin(BaseModelAdmin):
    pass

class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass

class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass

class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass


admin.site.register(GoodsType)
admin.site.register(IndexPromotionBanner)
admin.site.register(IndexGoodsBanner)
admin.site.register(IndexTypeGoodsBanner)
