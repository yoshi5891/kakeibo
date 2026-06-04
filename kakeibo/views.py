from django.shortcuts import render, redirect
from .models import Expense, Category
from .forms import UploadImageForm
from .utils.ocr import run_ocr
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from calendar import monthrange
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.conf import settings
from pathlib import Path
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
    "固定費": "#8BC34A",
    "(み)こづかい": "#FF43D3",
    "(よ)こづかい": "#434CFF",
}

CATEGORY_KEYWORDS = {
    "食費": ["マクドナルド", "すき家", "吉野家", "松屋", "ガスト", "すし", "ラーメン"],
    "交通費": ["バス", "JR", "地下鉄", "新幹線", "タクシー"],
    "日用品": ["ダイソー", "セリア", "薬局", "ドラッグ"],
    "交際費": ["映画", "カラオケ", "ゲーム"],
}

# ============================================================
#  今日だけ 500 を回避するために family = None に統一
# ============================================================

@login_required
def expense_create(request):
    family = None

    # --- カテゴリ追加後の戻りを判定（?from=category_add を使う） ---
    if request.GET.get('from') == 'category_add':
        return redirect('/add/')

    amount = request.GET.get('amount')
    date_param = request.GET.get('date')

    if request.method == 'POST':
        category_id = request.POST.get('category')
        category = Category.objects.get(id=category_id)

        Expense.objects.create(
            category=category,
            date=request.POST.get('date'),
            amount=request.POST.get('amount'),
            memo=request.POST.get('memo'),
        )
        return redirect('expense_list')

    initial = {}
    if amount:
        initial['amount'] = amount

    initial['date'] = date_param if date_param else date.today().strftime('%Y-%m-%d')

    category_param = request.GET.get('category')
    if category_param:
        initial['category'] = int(category_param)

    categories = Category.objects.all()

    for c in categories:
        last_expense = Expense.objects.filter(category=c).order_by('-date').first()
        c.last_used = last_expense.date if last_expense else date.min

    categories = sorted(categories, key=lambda c: c.last_used, reverse=True)

    return render(request, 'kakeibo/expense_form.html', {
        'categories': categories,
        'initial': initial,
    })

@login_required
def expense_list(request):
    family = None
    expenses = Expense.objects.all().order_by('-date')
    return render(request, 'kakeibo/expense_list.html', {'expenses': expenses})


@login_required
def expense_edit(request, pk):
    family = None
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

    categories = Category.objects.all()

    return render(request, 'kakeibo/expense_form.html', {
        'expense': expense,
        'categories': categories
    })


@login_required
def expense_delete(request, pk):
    family = None
    expense = get_object_or_404(Expense, pk=pk)
    expense.delete()
    return redirect('expense_list')


@login_required
def expense_summary(request):
    family = None

    today = timezone.now()
    month_start = today.replace(day=1)

    total = Expense.objects.filter(
        date__gte=month_start,
        date__lte=today
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'kakeibo/expense_summary.html', {
        'total': total,
        'month': today.strftime('%Y年%m月')
    })


@login_required
def expense_chart(request):
    family = None

    data = Expense.objects.values('category__name').annotate(total=Sum('amount'))

    labels = [item['category__name'] for item in data]
    totals = [item['total'] for item in data]

    return render(request, 'kakeibo/expense_chart.html', {
        'labels': labels,
        'totals': totals,
    })


@login_required
def expense_summary_month(request, year, month):
    family = None

    # 当月25日を締め日とする
    month_end = date(year, month, 25)
    month_start = month_end - relativedelta(months=1) + timedelta(days=1)

    total = Expense.objects.filter(
        date__gte=month_start,
        date__lte=month_end
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # 前月・翌月
    prev = month_end - relativedelta(months=1)
    next_ = month_end + relativedelta(months=1)

    return render(request, 'kakeibo/expense_summary_month.html', {
        'total': total,
        'year': year,
        'month': month,
        'prev_year': prev.year,
        'prev_month': prev.month,
        'next_year': next_.year,
        'next_month': next_.month,
    })

@login_required
def expense_filter(request):
    family = None
    expenses = None

    if request.method == 'POST':
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')

        if start and end:
            expenses = Expense.objects.filter(
                date__gte=start,
                date__lte=end
            ).order_by('date')

    return render(request, 'kakeibo/expense_filter.html', {'expenses': expenses})


@login_required
def expense_chart_bar(request):
    family = None

    data = Expense.objects.values('category__name').annotate(total=Sum('amount'))

    labels = [item['category__name'] for item in data]
    totals = [item['total'] for item in data]

    return render(request, 'kakeibo/expense_chart_bar.html', {
        'labels': labels,
        'totals': totals,
    })

@login_required
def dashboard(request):

    family = None

    month_str = request.GET.get('month')

    # 25日締めの基準日を決定
    if month_str:
        year, month = map(int, month_str.split('-'))
        target_date = date(year, month, 25)
    else:
        today = date.today()
        if today.day >= 26:
            target_date = date(today.year, today.month, 25)
        else:
            prev = today - relativedelta(months=1)
            target_date = date(prev.year, prev.month, 25)

    # 集計期間：前月26日〜当月25日
    start_date = target_date - relativedelta(months=1) + timedelta(days=1)
    end_date = target_date

    expenses = Expense.objects.filter(date__range=(start_date, end_date))

    # 日別集計
    days_in_month = (end_date - start_date).days + 1
    date_labels = [(start_date + timedelta(days=i)).day for i in range(days_in_month)]
    daily_totals = [0] * days_in_month

    for expense in expenses:
        day_index = (expense.date - start_date).days
        daily_totals[day_index] += expense.amount

    # 前月・翌月（正しく1ヶ月移動）
    prev_month_date = target_date - relativedelta(months=1)
    next_month_date = target_date + relativedelta(months=1)

    prev_month_str = prev_month_date.strftime('%Y-%m')
    next_month_str = next_month_date.strftime('%Y-%m')

    # 合計
    total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    # 前月合計
    prev_month_total = Expense.objects.filter(
        date__range=(
            prev_month_date - relativedelta(months=1) + timedelta(days=1),
            prev_month_date
        )
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    diff = total - prev_month_total
    diff_color = "red" if diff > 0 else "blue"

    # カテゴリ別
    data = expenses.values('category__name').annotate(total=Sum('amount'))
    labels = [item['category__name'] for item in data]
    totals = [item['total'] for item in data]
    colors = [CATEGORY_COLORS.get(item['category__name'], "#CCCCCC") for item in data]

    ranking = data.order_by('-total')[:3]
    recent_expenses = expenses.order_by('-date')[:5]

    display_month = target_date.strftime('%Y年%m月')

    today_total = Expense.objects.filter(
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
    family = None
    categories = Category.objects.all()

    for c in categories:
        c.count = Expense.objects.filter(category=c).count()
        c.color = CATEGORY_COLORS.get(c.name, "#CCCCCC")

    return render(request, 'kakeibo/category_list.html', {'categories': categories})


@login_required
def category_add(request):
    family = None

    if request.method == 'POST':
        name = request.POST.get('name')
        Category.objects.create(
            name=name,
        )
        return redirect('/add/?from=category_add')

    return render(request, 'kakeibo/category_form.html')


@login_required
def category_edit(request, pk):
    family = None
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.save()
        return redirect('category_list')

    return render(request, 'kakeibo/category_form.html', {'category': category})


@login_required
def category_delete(request, pk):
    family = None
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return redirect('category_list')


# --- OCR 関連はそのまま ---
def extract_total(text):
    # 全角 → 半角
    t = text.replace("￥", "¥").replace("円", "").replace("　", " ")
    t = t.replace(",", "").replace("．", ".").replace("。", ".")

    # よくある金額表現
    patterns = [
        r"合計[^\d]*(\d+)",          # 合計 1234
        r"ご請求金額[^\d]*(\d+)",    # ご請求金額 1234
        r"お買い上げ金額[^\d]*(\d+)",# お買い上げ金額 1234
        r"計[^\d]*(\d+)",            # 計 1234
        r"¥\s*(\d+)",                # ¥ 1234
        r"¥(\d+)",                   # ¥1234
        r"(\d+)\s*円",               # 1234円
        r"金額[^\d]*(\d+)",          # 金額 1234
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            return match.group(1)

    # fallback：数字が複数ある場合、最大値を合計とみなす
    numbers = re.findall(r"\d{3,}", t)
    if numbers:
        return max(numbers, key=lambda x: int(x))

    return None


def extract_date(text):
    # 全角 → 半角
    t = text.replace("年", "/").replace("月", "/").replace("日", "")
    t = t.replace("．", ".").replace("。", ".")
    t = t.replace("ー", "-").replace("―", "-").replace("−", "-")
    t = t.replace("／", "/").replace(" ", "")

    # パターン一覧（表記ゆれを全部拾う）
    patterns = [
        r"(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})",  # 2024/5/3, 2024-5-3
        r"(\d{4}\.\d{1,2}\.\d{1,2})",          # 2024.5.3
        r"(\d{2}[-/\.]\d{1,2}[-/\.]\d{1,2})",  # 24/5/3
        r"(\d{4}/\d{1,2}/\d{1,2})",            # 2024/05/03
        r"(\d{1,2}/\d{1,2})",                  # 5/3（年が無い場合 → 今年扱い）
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            date_str = match.group(1)

            # 年が無い場合は今年を補完
            if re.match(r"^\d{1,2}/\d{1,2}$", date_str):
                year = date.today().year
                return f"{year}/{date_str}"

            return date_str

    return None


def estimate_category(text):
    # OCR の表記ゆれ対策（全角 → 半角、スペース除去）
    t = text.replace("　", " ").replace(" ", "")
    t = t.lower()

    # カテゴリごとのキーワード辞書を使う
    for category, keywords in CATEGORY_KEYWORDS.items():
        for word in keywords:
            if word.lower() in t:
                return category

    # fallback：食べ物系の単語が多い場合 → 食費
    food_words = ["弁当", "定食", "ランチ", "カフェ", "パン", "寿司", "そば", "うどん"]
    if any(w in t for w in food_words):
        return "食費"

    # fallback：交通系
    transport_words = ["駅", "線", "バス", "タクシー"]
    if any(w in t for w in transport_words):
        return "交通費"

    # fallback：日用品
    daily_words = ["薬局", "ドラッグ", "ホームセンター"]
    if any(w in t for w in daily_words):
        return "日用品"

    return None


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

            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            text = pytesseract.image_to_string(thresh, lang='jpn')

            total = extract_total(text)
            date = extract_date(text)
            category_id = estimate_category(text)

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
    return render(request, "kakeibo/help.html")


from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('login')

from django.shortcuts import render
#from .forms import ReceiptForm
from .utils.ocr import run_ocr

def upload_receipt(request):
    text = None

    if request.method == "POST":
        form = UploadImageForm(request.POST, request.FILES)

        if form.is_valid():
            image = form.cleaned_data["image"]

            # 一時保存
            image_path = f"/tmp/{image.name}"
            with open(image_path, "wb+") as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            # --- 改良ポイント：前処理 + OCR ---
            text = run_ocr(image_path)

    else:
        form = UploadImageForm()

    return render(request, "upload_receipt.html", {"form": form, "text": text})

#ここからバックアップ復元機能
import requests
import subprocess
from django.http import HttpResponse
import os

GITHUB_OWNER = "yoshi5891"
GITHUB_REPO = "kakeibo"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

@login_required
def restore_data(request):

    if not request.user.is_superuser:
        return HttpResponse("Permission denied", status=403)

    if not GITHUB_TOKEN:
        return HttpResponse("ERROR: GITHUB_TOKEN is not set on the server.")

    # GitHub API から ZIP バックアップ一覧を取得
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/backups"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return HttpResponse(
            f"GitHub API Error<br>Status: {response.status_code}<br><pre>{response.text}</pre>"
        )

    res = response.json()

    # backup-YYYY-MM-DD.zip のみ抽出
    backups = [f for f in res if f["name"].startswith("backup-") and f["name"].endswith(".zip")]

    if not backups:
        return HttpResponse("No ZIP backup files found")

    # 最新 ZIP を選択
    latest = sorted(backups, key=lambda x: x["name"], reverse=True)[0]

    # ダウンロード URL
    download_url = latest["download_url"]

    # ZIP を取得
    download_response = requests.get(download_url)

    if download_response.status_code != 200:
        return HttpResponse(
            f"Backup download failed<br>Status: {download_response.status_code}<br><pre>{download_response.text}</pre>"
        )

    # ZIP を一時保存
    zip_path = "/tmp/restore.zip"
    with open(zip_path, "wb") as f:
        f.write(download_response.content)

    # ZIP を解凍
    import zipfile
    extract_dir = "/tmp/restore_zip"
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    # data.json を探す
    json_path = os.path.join(extract_dir, "data.json")
    if not os.path.exists(json_path):
        return HttpResponse("data.json not found inside ZIP")

    # loaddata 実行
    result = subprocess.run(
        ["python", "manage.py", "loaddata", json_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return HttpResponse(f"Restore failed<br><pre>{result.stderr}</pre>")

    return HttpResponse(
        f"""
        Restore completed.<br><br>
        File: {latest['name']}<br><br>
        Result:<br>
        <pre>{result.stdout}</pre>
        """
    )

@login_required
def backup_data(request):

    if not request.user.is_superuser:
        return HttpResponse("Permission denied", status=403)

    # --- ① dumpdata を JSON に出力 ---
    result = subprocess.run(
        [
            "python",
            "manage.py",
            "dumpdata",
            "kakeibo",
            "--indent",
            "2"
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return HttpResponse(f"Backup failed<br><pre>{result.stderr}</pre>")

    # JSON を一時保存
    json_path = "/tmp/backup.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(result.stdout)

    # --- ② ZIP を作成 ---
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_path = f"/tmp/backup-{timestamp}.zip"

    import zipfile
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(json_path, arcname="data.json")

        # .env があれば追加
        env_path = os.path.join(settings.BASE_DIR, ".env")
        if os.path.exists(env_path):
            zipf.write(env_path, arcname=".env")

        # metadata
        metadata_path = "/tmp/metadata.txt"
        with open(metadata_path, "w") as f:
            f.write(f"Backup created at: {timestamp}\n")
            f.write(f"User: {request.user}\n")
        zipf.write(metadata_path, arcname="metadata.txt")

    # --- ③ GitHub に ZIP をアップロード ---
    upload_result = subprocess.run(
        ["python", "backup_to_github.py", zip_path],
        capture_output=True,
        text=True
    )

    if upload_result.returncode != 0:
        return HttpResponse(
            f"GitHub upload failed<br><pre>{upload_result.stderr}</pre>"
        )

    return HttpResponse(
        f"""
        Backup completed.<br><br>
        File: backup-{timestamp}.zip<br><br>
        <pre>
        {upload_result.stdout}
        {upload_result.stderr}
        </pre>
        """
    )

BACKUP_TIME_FILE = "last_backup.txt"


def should_backup():
    from datetime import datetime, timedelta

    try:
        with open(BACKUP_TIME_FILE, "r") as f:
            last = datetime.fromisoformat(f.read().strip())

        return datetime.now() - last > timedelta(hours=24)

    except:
        return True

def save_backup_time():
    from datetime import datetime

    with open(BACKUP_TIME_FILE, "w") as f:
        f.write(datetime.now().isoformat())    