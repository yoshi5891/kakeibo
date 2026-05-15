from django.contrib import admin
from .models import Profile, Family, Category, Expense, FixedCost

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    pass

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

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
