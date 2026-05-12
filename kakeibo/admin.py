from django.contrib import admin
from .models import Category, Expense
from .models import FixedCost

admin.site.register(Category)
admin.site.register(Expense)
admin.site.register(FixedCost)

class FixedCostAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('name',)