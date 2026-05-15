from django.db import models
from django.contrib.auth.models import User

# --- 家族モデル ---
class Family(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# --- User と Family を紐付ける ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.family.name}"

# --- カテゴリ ---
class Category(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# --- 支出 ---
class Expense(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    amount = models.IntegerField()
    memo = models.CharField(max_length=200, blank=True)
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.amount}円"

# --- 固定費 ---
class FixedCost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField("固定費名", max_length=100)
    amount = models.IntegerField("金額")
    category = models.ForeignKey(Category, verbose_name="カテゴリ", on_delete=models.CASCADE)
    created_at = models.DateTimeField("登録日", auto_now_add=True)

    class Meta:
        verbose_name = "固定費"
        verbose_name_plural = "固定費一覧"
