from calendar import monthrange
from datetime import date

from dateutil.relativedelta import relativedelta

from .models import Expense, FixedCost


def sync_fixed_costs(upto=None):
    """有効な固定費について、最終生成月の翌月から upto 月までの Expense を自動作成する。

    生成済みかどうかは last_generated（生成カーソル）で判定する。Expense の存在有無では
    判定しない。ユーザーが生成済みの支出を削除しても、その月は「生成済み」のまま扱われ、
    次回アクセス時に再生成されないようにするため。
    """
    upto = upto or date.today()
    upto_month_start = date(upto.year, upto.month, 1)

    for fc in FixedCost.objects.filter(is_active=True):
        if fc.last_generated:
            cursor = date(fc.last_generated.year, fc.last_generated.month, 1) + relativedelta(months=1)
        else:
            cursor = date(fc.start_date.year, fc.start_date.month, 1)

        while cursor <= upto_month_start:
            day = min(fc.day, monthrange(cursor.year, cursor.month)[1])
            Expense.objects.create(
                category=fc.category,
                date=date(cursor.year, cursor.month, day),
                amount=fc.amount,
                memo=fc.name,
                fixed_cost=fc,
            )
            fc.last_generated = cursor
            fc.save(update_fields=['last_generated'])
            cursor += relativedelta(months=1)
