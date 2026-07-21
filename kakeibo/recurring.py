from calendar import monthrange
from datetime import date

from dateutil.relativedelta import relativedelta

from .models import Expense, FixedCost


def sync_fixed_costs(upto=None):
    """有効な固定費について、登録月から upto 月までの未生成分の Expense を自動作成する。"""
    upto = upto or date.today()
    upto_month_start = date(upto.year, upto.month, 1)

    for fc in FixedCost.objects.filter(is_active=True):
        cursor = date(fc.start_date.year, fc.start_date.month, 1)

        while cursor <= upto_month_start:
            already_exists = Expense.objects.filter(
                fixed_cost=fc,
                date__year=cursor.year,
                date__month=cursor.month,
            ).exists()

            if not already_exists:
                day = min(fc.day, monthrange(cursor.year, cursor.month)[1])
                Expense.objects.create(
                    category=fc.category,
                    date=date(cursor.year, cursor.month, day),
                    amount=fc.amount,
                    memo=fc.name,
                    fixed_cost=fc,
                )

            cursor += relativedelta(months=1)
