from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Profile, Family, Category, Expense, FixedCost

# --- Profile を User の下に表示するための Inline ---
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False

# --- UserAdmin を拡張して Profile を紐づける ---
class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]

# 既存の UserAdmin を置き換える
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# --- 以下はあなたが作った Admin 設定 ---
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
    list_display = ('name', 'amount', 'category', 'day', 'start_date', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
