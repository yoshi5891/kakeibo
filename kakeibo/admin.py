from django.contrib import admin
from .models import Category, Expense, FixedCost
from .models import Profile

admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Expense)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)  # 一覧に表示する項目
    search_fields = ('name',)        # 名前で検索

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'amount', 'category')
    list_filter = ('category', 'date')
    search_fields = ('memo',)

@admin.register(FixedCost)
class FixedCostAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('name',)


