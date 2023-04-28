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


admin.site.register(UnpaidUser, UnpaidUserAdmin)
admin.site.register(PaidUser, PaidUserAdmin)
admin.site.register(UserCalories, UserCaloriesAdmin)
admin.site.register(FinishedUser, FinishedUserAdmin)
admin.site.register(SupportTicket, SupportTicketAdmin)
admin.site.register(BankCards, BankCardsAdmin)