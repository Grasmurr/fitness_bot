from django.contrib import admin
from .models import Категории, DailyContent, UnpaidUserContent
from django.db.models import Count


class BaseContentAdmin(admin.ModelAdmin):
    list_display = ('day', 'content_type', 'category')
    list_filter = ('category',)
    search_fields = ('category__название',)
    ordering = ('day',)

    fieldsets = (
        ('Основная информация', {
            'fields': ('day', 'category')
        }),
        ('Тип контента', {
            'fields': ('content_type', 'video', 'photo', 'gif', 'caption')
        }),
        ('Дополнительная информация', {
            'fields': ('sequence_number',)
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(category_count=Count('category'))
        return queryset


class DailyContentAdmin(BaseContentAdmin):
    ordering = ('category', 'day')


class UnpaidUserContentAdmin(admin.ModelAdmin):
    list_display = ('day', 'content_type')
    ordering = ('day',)

    fieldsets = (
        ('Основная информация', {
            'fields': ('day',)
        }),
        ('Тип контента', {
            'fields': ('content_type', 'video', 'photo', 'gif', 'caption')
        }),
        ('Дополнительная информация', {
            'fields': ('sequence_number',)
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset


admin.site.register(DailyContent, DailyContentAdmin)
admin.site.register(Категории)
admin.site.register(UnpaidUserContent, UnpaidUserContentAdmin)