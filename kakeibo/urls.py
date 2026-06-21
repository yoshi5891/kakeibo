from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('list/', views.expense_list, name='expense_list'),
    path('add/', views.expense_create, name='expense_create'),
    path('edit/<int:pk>/', views.expense_edit, name='expense_edit'),
    path('delete/<int:pk>/', views.expense_delete, name='expense_delete'),

    path('summary/', views.expense_summary, name='expense_summary'),
    path('summary/<int:year>/<int:month>/', views.expense_summary_month, name='expense_summary_month'),

    path('filter/', views.expense_filter, name='expense_filter'),

    path('chart/', views.expense_chart, name='expense_chart'),
    path('chart/bar/', views.expense_chart_bar, name='expense_chart_bar'),

    # カテゴリ管理
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    path("backup/", views.backup_data, name="backup"),
    path('restore_data/', views.restore_data, name='restore_data'),
    path("backup_list/", views.backup_list, name="backup_list"),
    path('special/', views.special_list, name='special_list'),
    path('special/add/', views.special_create, name='special_create'),
    path('special/<int:pk>/edit/', views.special_edit, name='special_edit'),

    # ログイン・ログアウト
    path('login/', auth_views.LoginView.as_view(template_name='kakeibo/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # OCR
    path('upload/', views.upload_image, name='upload_image'),

    # Help
    path("help/", views.help_page, name="help"),
]
