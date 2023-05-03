from django.contrib import admin
from .models import UnpaidUser, PaidUser, UserCalories, BankCards, FinishedUser, SupportTicket
from .views import export_to_xlsx


def export_to_xlsx_action(modeladmin, request, queryset):
    model_class = modeladmin.model
    return export_to_xlsx(model_class)


export_to_xlsx_action.short_description = "Выгрузить выбранные объекты в xlsx"


class UnpaidUserAdmin(admin.ModelAdmin):
    actions = [export_to_xlsx_action]


class PaidUserAdmin(admin.ModelAdmin):
    actions = [export_to_xlsx_action]


class UserCaloriesAdmin(admin.ModelAdmin):
    actions = [export_to_xlsx_action]


class FinishedUserAdmin(admin.ModelAdmin):
    actions = [export_to_xlsx_action]


class SupportTicketAdmin(admin.ModelAdmin):
    actions = [export_to_xlsx_action]


class BankCardsAdmin(admin.ModelAdmin):
    actions = [export_to_xlsx_action]


class MyAdminSite(admin.AdminSite):
    site_header = "Админ панель 21FIT"


my_admin_site = MyAdminSite(name='myadmin')
my_admin_site.register(UnpaidUser, UnpaidUserAdmin)
my_admin_site.register(PaidUser, PaidUserAdmin)
my_admin_site.register(UserCalories, UserCaloriesAdmin)
my_admin_site.register(FinishedUser, FinishedUserAdmin)
my_admin_site.register(SupportTicket, SupportTicketAdmin)
my_admin_site.register(BankCards, BankCardsAdmin)