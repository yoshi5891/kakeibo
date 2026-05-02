from django.shortcuts import render, redirect
from .models import Expense, Category
from .forms import UploadImageForm
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.db.models import Sum
from calendar import monthrange
from datetime import date
from datetime import datetime
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
import pytesseract
from PIL import Image
import re
import cv2
import numpy as np

# --- カテゴリごとの固定色設定 ---
CATEGORY_COLORS = {
    "食費": "#FF6384",
    "日用品": "#36A2EB",
    "交通費": "#FFCE56",
    "交際費": "#4BC0C0",
    "その他": "#9966FF",
}

CATEGORY_KEYWORDS = {
    "食費": ["マクドナルド", "すき家", "吉野家", "松屋", "ガスト", "すし", "ラーメン"],
    "交通費": ["バス", "JR", "地下鉄", "新幹線", "タクシー"],
    "日用品": ["ダイソー", "セリア", "薬局", "ドラッグ"],
    "交際費": ["映画", "カラオケ", "ゲーム"],
}

@login_required
def expense_create(request):
    # URLパラメータから値を取得（OCR から渡ってくる）
    amount = request.GET.get('amount')
    date_param = request.GET.get('date')

    if request.method == 'POST':
        category_id = request.POST.get('category')
        category = Category.objects.get(id=category_id)

        Expense.objects.create(
            user=request.user,
            category=category,
            date=request.POST.get('date'),
            amount=request.POST.get('amount'),
            memo=request.POST.get('memo'),
        )
        return redirect('expense_list')

    # 初期値をセット
    initial = {}

    # 金額（OCR）
    if amount:
        initial['amount'] = amount

    # 日付（OCR → なければ今日）
    if date_param:
        initial['date'] = date_param
    else:
        initial['date'] = date.today().strftime('%Y-%m-%d')

    # カテゴリ（OCR）
    category_param = request.GET.get('category')
    if category_param:
        initial['category'] = int(category_param)

    categories = Category.objects.filter(user=request.user)

    # カテゴリごとに「最後に使った日」を付与
    for c in categories:
        last_expense = Expense.objects.filter(user=request.user, category=c).order_by('-date').first()
        c.last_used = last_expense.date if last_expense else date.min

    # 最後に使った順に並べる
    categories = sorted(categories, key=lambda c: c.last_used, reverse=True)
    
    return render(request, 'kakeibo/expense_form.html', {
        'categories': categories,
        'initial': initial,
    })

@login_required
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    return render(request, 'kakeibo/expense_list.html', {'expenses': expenses})

@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)

    if request.method == 'POST':
        category_id = request.POST.get('category')
        category = Category.objects.get(id=category_id)

        expense.date = request.POST.get('date')
        expense.category = category
        expense.amount = request.POST.get('amount')
        expense.memo = request.POST.get('memo')
        expense.save()

        return redirect('expense_list')

    categories = Category.objects.filter(user=request.user).order_by('name')
    return render(request, 'kakeibo/expense_form.html', {
        'expense': expense,
        'categories': categories
    })

@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense.delete()
    return redirect('expense_list')

@login_required
def expense_summary(request):
    today = timezone.now()
    month_start = today.replace(day=1)

    total = Expense.objects.filter(
        user=request.user,
        date__gte=month_start,
        date__lte=today
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'kakeibo/expense_summary.html', {
        'total': total,
        'month': today.strftime('%Y年%m月')
    })

@login_required
def expense_chart(request):
    # カテゴリ別の合計金額を集計
    data = Expense.objects.values('category__name').annotate(total=Sum('amount'))

    labels = [item['category__name'] for item in data]
    totals = [item['total'] for item in data]
    colors = [CATEGORY_COLORS.get(item['category__name'], "#CCCCCC") for item in data]

    return render(request, 'kakeibo/expense_chart.html', {
        'labels': labels,
        'totals': totals,
    })

@login_required
def expense_summary_month(request, year, month):
    # 月初と月末を計算
    month_start = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    month_end = date(year, month, last_day)

    # 合計金額
    total = Expense.objects.filter(
        user=request.user,
        date__gte=month_start,
        date__lte=month_end
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # 前月・翌月の計算
    prev_year = year if month > 1 else year - 1
    prev_month = month - 1 if month > 1 else 12

    next_year = year if month < 12 else year - 1
    next_month = month + 1 if month < 12 else 1

    return render(request, 'kakeibo/expense_summary_month.html', {
        'total': total,
        'year': year,
        'month': month,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
    })

@login_required
def expense_filter(request):
    expenses = None

    if request.method == 'POST':
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')

        if start and end:
            expenses = Expense.objects.filter(
                date__gte=start,
                date__lte=end
            ).order_by('date')

    return render(request, 'kakeibo/expense_filter.html', {
        'expenses': expenses
    })

#カテゴリ別の合計を取得
@login_required
def expense_chart_bar(request):
    data = Expense.objects.values('category__name').annotate(total=Sum('amount'))

    labels = [item['category__name'] for item in data]
    totals = [item['total'] for item in data]

    return render(request, 'kakeibo/expense_chart_bar.html', {
        'labels': labels,
        'totals': totals,
    })

@login_required
def dashboard(request):
    # --- 月パラメータの取得 ---
    month_str = request.GET.get('month')

    if month_str:
        year, month = map(int, month_str.split('-'))
        target_date = date(year, month, 1)
    else:
        target_date = date.today().replace(day=1)

    # 月初と月末
    start_date = target_date
    end_date = (target_date + relativedelta(months=1)) - timedelta(days=1)

    # ⭐ 対象月の支出だけを取得（ここで expenses を定義）
    expenses = Expense.objects.filter(
        user=request.user,
        date__range=(start_date, end_date)
    )

    # 月の日数を取得
    days_in_month = (end_date - start_date).days + 1

    # 日付リスト（1日〜末日）
    date_labels = [(start_date + timedelta(days=i)).day for i in range(days_in_month)]

    # 日別の合計金額を初期化（全部0円）
    daily_totals = [0] * days_in_month

    # 実際の支出を日別に集計
    for expense in expenses:
        day_index = expense.date.day - 1
        daily_totals[day_index] += expense.amount


    # --- 前月・翌月の計算 ---
    prev_month_date = target_date - relativedelta(months=1)
    next_month_date = target_date + relativedelta(months=1)

    prev_month_str = prev_month_date.strftime('%Y-%m')
    next_month_str = next_month_date.strftime('%Y-%m')

    # ⭐ 合計金額
    total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    # --- 前月の支出合計を計算 ---
    prev_month_date = target_date - relativedelta(months=1)
    prev_year = prev_month_date.year
    prev_month_num = prev_month_date.month

    prev_month_total = Expense.objects.filter(
        user=request.user,
        date__year=prev_year,
        date__month=prev_month_num
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # 今月との差分
    diff = total - prev_month_total

    # 増減の色（プラスなら赤、マイナスなら青）
    diff_color = "red" if diff > 0 else "blue"



    # ⭐ 円グラフ・棒グラフ用データ
    data = expenses.values('category__name').annotate(total=Sum('amount'))
    labels = [item['category__name'] for item in data]
    totals = [item['total'] for item in data]

    # --- カテゴリ別ランキング（トップ3） ---
    ranking = data.order_by('-total')[:3]

    # ⭐ カテゴリごとの色リストを作成
    colors = [CATEGORY_COLORS.get(item['category__name'], "#CCCCCC") for item in data]


    # ⭐ 最近の支出5件
    recent_expenses = expenses.order_by('-date')[:5]

    # 表示用の月（例：2026年03月）
    display_month = target_date.strftime('%Y年%m月')

    #「今日の支出合計」を追加
    today_total = Expense.objects.filter(
        user=request.user,
        date=date.today()
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'kakeibo/dashboard.html', {
        'total': total,
        'month': display_month,
        'labels': labels,
        'totals': totals,
        'recent_expenses': recent_expenses,
        'prev_month': prev_month_str,
        'next_month': next_month_str,
        'colors': colors,
        'date_labels': date_labels,
        'daily_totals': daily_totals,
        'ranking': ranking,
        'today_total': today_total,
        'prev_month_total': prev_month_total,
        'diff': diff,
        'diff_color': diff_color,


    })

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user).order_by('name')
    for c in categories:
        c.count = Expense.objects.filter(user=request.user, category=c).count()
        c.color = CATEGORY_COLORS.get(c.name, "#CCCCCC") 

    return render(request, 'kakeibo/category_list.html', {'categories': categories})

#カテゴリ追加機能実装
@login_required
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        Category.objects.create(
            name=name,
            user=request.user  # ← これを追加
        )
        return redirect('category_list')

    return render(request, 'kakeibo/category_form.html')

#カテゴリ編集機能実装
@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)

    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.save()
        return redirect('category_list')

    return render(request, 'kakeibo/category_form.html', {'category': category})

#カテゴリ削除機能実装
@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    category.delete()
    return redirect('category_list')

# 合計金額抽出関数（関数の外に置く）
def extract_total(text):
    # 合計の誤読パターンを広くカバー
    patterns = [
        r"合計[^\d]*([\d,\.]+)",     # 合計 22,032 / 合計¥22,032
        r"合\s*計[^\d]*([\d,\.]+)",  # 合 計 22,032
        r"計[^\d]*([\d,\.]+)",       # 計 22,032（誤読パターン）
        r"半[^\d]*([\d,\.]+)",       # 半 22.032（Tesseractの誤読）
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1)
            value = value.replace(",", "").replace(".", "")
            return value
    return None

def extract_date(text):
    patterns = [
        r"(\d{4}\s*[-/\.]\s*\d{1,2}\s*[-/\.]\s*\d{1,2})",  # 空白入り対応
        r"(\d{4}年\s*\d{1,2}月\s*\d{1,2}日)",              # 和暦＋空白対応
        r"(\d{2}\s*[-/\.]\s*\d{1,2}\s*[-/\.]\s*\d{1,2})",  # 2桁年対応（24/5/8）
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).replace(" ", "")
    return None

def estimate_category(text):
    text = text.lower()

    if "マック" in text or "バーガー" in text:
        return 1
    if "電車" in text or "バス" in text:
        return 2
    if "日用品" in text:
        return 3
    if "交際" in text:
        return 4

    return None

#アップロード
def upload_image(request):
    text = None
    total = None
    date = None
    category_id = None

    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)

        if form.is_valid():
            image_file = form.cleaned_data['image']
            image = Image.open(image_file)

            mode = request.POST.get("mode", "normal")

            if mode == "normal":
                # --- 標準前処理 ---
                img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (3, 3), 0)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            elif mode == "receipt":
                # --- 薄い印字レシート向け ---
                img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)
                gray = cv2.medianBlur(gray, 3)
                thresh = cv2.adaptiveThreshold(
                    gray, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    31, 2
                )

            elif mode == "smaregi":
                # --- スマレジ専用前処理 ---
                img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)
                gray = cv2.medianBlur(gray, 3)
                thresh = cv2.adaptiveThreshold(
                    gray, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    31, 2
                )
            
            # OCR

            from PIL import Image as PilImage
            PilImage.fromarray(thresh).save("debug_thresh.png")

            text = pytesseract.image_to_string(thresh, lang='jpn')

            print("★★★ OCR結果 ★★★")
            print(repr(text))

            # --- 抽出 ---
            total = extract_total(text)
            date = extract_date(text)
            category_id = estimate_category(text)

            # ★★★ 元の動作：/add/ にパラメータ付きで飛ばす ★★★
            params = []
            if total:
                params.append(f"amount={total}")
            if date:
                params.append(f"date={date}")
            if category_id:
                params.append(f"category={category_id}")

            if params:
                query = "&".join(params)
                return redirect(f"/add/?{query}")
            else:
                return redirect("/add/")

    # GET の場合
    return render(request, 'kakeibo/upload.html', {
        'form': UploadImageForm(),
        'text': text,
    })

def guess_category(text):
    for category, keywords in CATEGORY_KEYWORDS.items():
        for word in keywords:
            if word in text:
                return category
    return None

def help_page(request):
    return render(request, "help.html")


