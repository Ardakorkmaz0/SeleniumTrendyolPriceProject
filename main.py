import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
import time
import tkinter as tk
from tkinter import ttk
import threading
import re
import statistics

CATEGORIES = [
    ("Kadın",            "Women",            "/butik/liste/1/kadin",        "👗"),
    ("Erkek",            "Men",              "/butik/liste/2/erkek",        "👔"),
    ("Anne & Çocuk",     "Mom & Kids",       "/butik/liste/3/anne-cocuk",   "👶"),
    ("Ev & Yaşam",       "Home & Living",    "/butik/liste/4/ev-yasam",     "🏠"),
    ("Süpermarket",      "Grocery",          "/butik/liste/6/supermarket",  "🛒"),
    ("Kozmetik",         "Cosmetics",        "/butik/liste/7/kozmetik",     "💄"),
    ("Ayakkabı & Çanta", "Shoes & Bags",     "/butik/liste/8/ayakkabi-canta","👟"),
    ("Elektronik",       "Electronics",      "/butik/liste/5/elektronik",   "💻"),
    ("Saat & Aksesuar",  "Watch & Accessory","/butik/liste/10/saat-aksesuar","⌚"),
    ("Spor & Outdoor",   "Sports & Outdoor", "/butik/liste/9/spor-outdoor", "⚽"),
    ("Flaş Ürünler",     "Flash Products",   "/flash-urunler",             "⚡"),
    ("Çok Satanlar",     "Best Sellers",     "/cok-satanlar",              "🔥"),
]

TEXTS = {
    "tr": {
        "title":        "Trendyol Fiyat Tarayıcı",
        "subtitle":     "Bir kategori seçin ve fiyatları tarayın",
        "lang_btn":     "🇬🇧 English",
        "status_ready":  "Hazır — bir kategori seçin",
        "status_loading":"⏳  {cat} yükleniyor...",
        "status_scroll": "⏳  Popüler ürünler kaydırılıyor... ({n} ürün)",
        "status_scan":   "⏳  Sayfa taranıyor... ({n} fiyat bulundu)",
        "status_done":   "✅  Tamamlandı — {n} fiyat bulundu",
        "total":         "Toplam {n} fiyat:",
        "clear":         "Temizle",
        "export":        "Dışa Aktar (.txt)",
        "exported":      "✅  {path} dosyasına kaydedildi",
        "stats_title":   "Fiyat İstatistikleri",
        "stat_count":    "Ürün Sayısı",
        "stat_min":      "En Düşük",
        "stat_max":      "En Yüksek",
        "stat_avg":      "Ortalama",
        "stat_median":   "Medyan",
        "stat_range":    "Fiyat Aralığı",
        "stat_under100": "100 TL Altı",
        "stat_100_500":  "100-500 TL",
        "stat_500_1k":   "500-1000 TL",
        "stat_over1k":   "1000 TL Üstü",
        "stat_na":       "—",
        "show_prices":   "Fiyat Listesi",
        "show_stats":    "İstatistikler",
        "show_dist":     "Dağılım",
    },
    "en": {
        "title":        "Trendyol Price Scraper",
        "subtitle":     "Pick a category and scrape the prices",
        "lang_btn":     "🇹🇷 Türkçe",
        "status_ready":  "Ready — pick a category",
        "status_loading":"⏳  Loading {cat}...",
        "status_scroll": "⏳  Scrolling popular products... ({n} items)",
        "status_scan":   "⏳  Scanning page... ({n} prices found)",
        "status_done":   "✅  Done — {n} prices found",
        "total":         "Total {n} prices:",
        "clear":         "Clear",
        "export":        "Export (.txt)",
        "exported":      "✅  Saved to {path}",
        "stats_title":   "Price Statistics",
        "stat_count":    "Product Count",
        "stat_min":      "Lowest",
        "stat_max":      "Highest",
        "stat_avg":      "Average",
        "stat_median":   "Median",
        "stat_range":    "Price Range",
        "stat_under100": "Under 100 TL",
        "stat_100_500":  "100-500 TL",
        "stat_500_1k":   "500-1000 TL",
        "stat_over1k":   "Over 1000 TL",
        "stat_na":       "—",
        "show_prices":   "Price List",
        "show_stats":    "Statistics",
        "show_dist":     "Distribution",
    },
}

BG          = "#1a1a2e"
BG_CARD     = "#16213e"
BG_BTN      = "#0f3460"
BG_BTN_HOVER= "#1a5276"
FG          = "#e0e0e0"
FG_DIM      = "#8899aa"
ACCENT      = "#e94560"
BG_LOG      = "#0d1117"
FG_LOG      = "#c9d1d9"
GREEN       = "#3fb950"
RED         = "#f85149"
BLUE        = "#58a6ff"
PURPLE      = "#bc8cff"

COLLECT_JS = """
    let results = [];
    let container = arguments[0] || document;
    container.querySelectorAll('div.current-price__current').forEach(el => {
        let card = el.closest('a') || el.closest('li') || el.closest('div[data-testid]');
        let name = card?.querySelector('[class*="information"], [class*="product-name"], [class*="description"]')?.textContent?.trim() || 'Unknown';
        let price = el.textContent.trim();
        if (price) results.push(name + ' | ' + price);
    });
    return results;
"""

driver = uc.Chrome(version_main=146)
lang = "tr"
current_prices = []


def t(key, **kw):
    return TEXTS[lang][key].format(**kw) if kw else TEXTS[lang][key]


def parse_price(price_str):
    cleaned = price_str.replace(".", "").replace(",", ".").strip()
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    try:
        return float(cleaned)
    except:
        return None


def fmt_price(val):
    if val >= 1000:
        return f"{val:,.2f} TL".replace(",", ".")
    return f"{val:.2f} TL"


def init_driver():
    global driver
    if driver is not None:
        return
    driver = uc.Chrome()
    driver.maximize_window()
    driver.get("https://www.trendyol.com/")
    try:
        WebDriverWait(driver, 5).until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH, "/html/body/div[2]/div/div/div[2]/img")
            )
        )
        driver.find_element(By.XPATH, "/html/body/div[2]/div/div/div[2]/img").click()
        time.sleep(1)
    except:
        pass


def close_popup():
    try:
        WebDriverWait(driver, 3).until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH, "/html/body/div[2]/div/div/div[2]/img")
            )
        )
        driver.find_element(By.XPATH, "/html/body/div[2]/div/div/div[2]/img").click()
        time.sleep(1)
    except:
        pass


def scroll_widget_ul():
    collected = set()
    try:
        widget = driver.execute_script("""
            let headers = document.querySelectorAll('h2, h3, div, span');
            for (let h of headers) {
                if (h.textContent.trim().startsWith('Popüler Ürünler')) {
                    return h.closest('.widget') || h.closest('[class*="widget"]') || h.parentElement?.parentElement;
                }
            }
            return null;
        """)
        if not widget:
            return collected

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", widget)
        time.sleep(1)

        items = driver.execute_script(COLLECT_JS, widget)
        collected.update(items)
        set_status(t("status_scroll", n=len(collected)))

        for _ in range(100):
            arrow = driver.execute_script("""
                let w = arguments[0];
                let btns = w.querySelectorAll('button, div.slider-arrow, [data-testid="slider-arrow"]');
                let right = null;
                for (let b of btns) {
                    let rect = b.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) right = b;
                }
                return right;
            """, widget)
            if not arrow:
                break
            driver.execute_script("arguments[0].click();", arrow)
            time.sleep(0.5)

            items = driver.execute_script(COLLECT_JS, widget)
            collected.update(items)
            set_status(t("status_scroll", n=len(collected)))
    except:
        pass
    return collected


def scrape_category(cat_tr, cat_en, cat_path):
    global driver, current_prices
    cat_name = cat_tr if lang == "tr" else cat_en

    set_status(t("status_loading", cat=cat_name))
    log_clear()
    clear_stats()
    log(f"{'━'*52}")
    log(f"  {cat_name}")
    log(f"{'━'*52}\n")

    init_driver()

    driver.get("https://www.trendyol.com" + cat_path)
    time.sleep(2)
    close_popup()

    slider_data = scroll_widget_ul()

    prev_count = 0
    for _ in range(20):
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.8)

        try:
            more_btn = driver.find_element(
                By.XPATH, '//div[contains(text(),"Daha fazla göster")]'
            )
            driver.execute_script("arguments[0].click();", more_btn)
            time.sleep(2)
        except:
            pass

        count = len(driver.find_elements(By.CSS_SELECTOR, "div.current-price__current"))
        set_status(t("status_scan", n=count))
        if count == prev_count:
            break
        prev_count = count

    scroll_data = driver.execute_script(COLLECT_JS, None)

    all_products = slider_data.union(set(scroll_data))

    current_prices = []
    for p in all_products:
        price_str = p.split("|")[-1].strip()
        val = parse_price(price_str)
        if val and val > 0:
            current_prices.append(val)

    current_prices.sort()

    show_prices_tab()
    update_stats()
    set_status(t("status_done", n=len(current_prices)))
    set_buttons_state("normal")


def show_prices_tab():
    log_clear()
    if not current_prices:
        return
    log(f"  {t('total', n=len(current_prices))}\n")
    for i, p in enumerate(current_prices):
        log(f"  {i+1:>4}.  {fmt_price(p)}")


def show_stats_tab():
    log_clear()
    if not current_prices:
        return
    prices = current_prices
    avg = statistics.mean(prices)
    med = statistics.median(prices)
    mn = min(prices)
    mx = max(prices)

    log(f"  {t('stats_title')}")
    log(f"  {'─'*40}\n")
    log(f"  {t('stat_count'):.<28} {len(prices):>10}")
    log(f"  {t('stat_min'):.<28} {fmt_price(mn):>10}")
    log(f"  {t('stat_max'):.<28} {fmt_price(mx):>10}")
    log(f"  {t('stat_avg'):.<28} {fmt_price(avg):>10}")
    log(f"  {t('stat_median'):.<28} {fmt_price(med):>10}")
    log(f"  {t('stat_range'):.<28} {fmt_price(mx - mn):>10}")
    if len(prices) >= 2:
        stdev = statistics.stdev(prices)
        log(f"  {'Std. Sapma / Std. Dev.':.<28} {fmt_price(stdev):>10}")


def show_dist_tab():
    log_clear()
    if not current_prices:
        return
    prices = current_prices
    total = len(prices)

    brackets = [
        (t("stat_under100"), 0, 100),
        (t("stat_100_500"),  100, 500),
        (t("stat_500_1k"),   500, 1000),
        (t("stat_over1k"),   1000, float("inf")),
    ]

    bar_max = 30
    counts = []
    max_c = 0
    for label, lo, hi in brackets:
        c = sum(1 for p in prices if lo <= p < hi)
        counts.append((label, c))
        if c > max_c:
            max_c = c

    log(f"  {t('stats_title')} — {t('show_dist')}")
    log(f"  {'─'*48}\n")
    for label, c in counts:
        pct = (c / total * 100) if total > 0 else 0
        bar_len = int((c / max_c) * bar_max) if max_c > 0 else 0
        log(f"  {label:<16} {'█' * bar_len:<{bar_max}}  {c:>4} ({pct:>5.1f}%)")

    log("")
    sorted_p = sorted(prices)
    q1 = sorted_p[len(sorted_p) // 4]
    q2 = sorted_p[len(sorted_p) // 2]
    q3 = sorted_p[(3 * len(sorted_p)) // 4]
    log(f"  {'Q1 (25%)':.<28} {fmt_price(q1):>10}")
    log(f"  {'Q2 (50%)':.<28} {fmt_price(q2):>10}")
    log(f"  {'Q3 (75%)':.<28} {fmt_price(q3):>10}")


def update_stats():
    if not current_prices:
        clear_stats()
        return
    prices = current_prices
    data = {
        "count": (str(len(prices)),          FG),
        "min":   (fmt_price(min(prices)),     GREEN),
        "max":   (fmt_price(max(prices)),     RED),
        "avg":   (fmt_price(statistics.mean(prices)),   BLUE),
        "median":(fmt_price(statistics.median(prices)), PURPLE),
    }
    for key, (val, clr) in data.items():
        lbl = stat_values[key]
        lbl.after(0, lambda l=lbl, v=val, c=clr: l.config(text=v, fg=c))


def clear_stats():
    for lbl in stat_values.values():
        lbl.after(0, lambda l=lbl: l.config(text=t("stat_na"), fg=FG_DIM))


def on_category_click(cat_tr, cat_en, cat_path):
    set_buttons_state("disabled")
    threading.Thread(
        target=scrape_category, args=(cat_tr, cat_en, cat_path), daemon=True
    ).start()


def on_tab_click(tab_fn, idx):
    if not current_prices:
        return
    for i, b in enumerate(tab_buttons):
        if i == idx:
            b.config(bg=ACCENT, fg="#ffffff")
        else:
            b.config(bg=BG_CARD, fg=FG)
    tab_fn()


def toggle_language():
    global lang
    lang = "en" if lang == "tr" else "tr"
    refresh_ui()


def refresh_ui():
    root.title(t("title"))
    title_label.config(text=t("title"))
    subtitle_label.config(text=t("subtitle"))
    lang_btn.config(text=t("lang_btn"))
    clear_btn.config(text=t("clear"))
    export_btn.config(text=t("export"))
    status_label.config(text=t("status_ready"))
    tab_buttons[0].config(text=t("show_prices"))
    tab_buttons[1].config(text=t("show_stats"))
    tab_buttons[2].config(text=t("show_dist"))
    for key, lbl in stat_labels.items():
        lbl.config(text=t(f"stat_{key}"))
    for i, (cat_tr, cat_en, _, emoji) in enumerate(CATEGORIES):
        name = cat_tr if lang == "tr" else cat_en
        buttons[i].config(text=f"{emoji}  {name}")


def log(msg):
    log_text.after(0, lambda m=msg: _append(m))

def _append(msg):
    log_text.config(state="normal")
    log_text.insert(tk.END, msg + "\n")
    log_text.see(tk.END)
    log_text.config(state="disabled")

def log_clear():
    log_text.after(0, _clear)

def _clear():
    log_text.config(state="normal")
    log_text.delete("1.0", tk.END)
    log_text.config(state="disabled")

def set_status(msg):
    status_label.after(0, lambda m=msg: status_label.config(text=m))

def set_buttons_state(state):
    for btn in buttons:
        btn.after(0, lambda b=btn, s=state: b.config(state=s))

def on_export():
    content = log_text.get("1.0", tk.END).strip()
    if not content:
        return
    path = "trendyol_export.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    set_status(t("exported", path=path))

def on_close():
    global driver
    if driver:
        driver.quit()
    root.destroy()


root = tk.Tk()
root.title(t("title"))
root.geometry("1020x780")
root.minsize(860, 600)
root.configure(bg=BG)
root.protocol("WM_DELETE_WINDOW", on_close)

header = tk.Frame(root, bg=BG, pady=12)
header.pack(fill="x", padx=20)

title_frame = tk.Frame(header, bg=BG)
title_frame.pack(side="left")

title_label = tk.Label(
    title_frame, text=t("title"),
    font=("Segoe UI", 18, "bold"), fg=ACCENT, bg=BG
)
title_label.pack(anchor="w")

subtitle_label = tk.Label(
    title_frame, text=t("subtitle"),
    font=("Segoe UI", 10), fg=FG_DIM, bg=BG
)
subtitle_label.pack(anchor="w")

lang_btn = tk.Button(
    header, text=t("lang_btn"),
    font=("Segoe UI", 10), fg=FG, bg=BG_CARD,
    activebackground=BG_BTN_HOVER, activeforeground=FG,
    bd=0, padx=14, pady=6, cursor="hand2",
    command=toggle_language
)
lang_btn.pack(side="right", pady=(4, 0))

sep = tk.Frame(root, bg=ACCENT, height=2)
sep.pack(fill="x", padx=20)

cats_frame = tk.Frame(root, bg=BG, pady=10)
cats_frame.pack(fill="x", padx=20)

buttons = []
for idx, (cat_tr, cat_en, path, emoji) in enumerate(CATEGORIES):
    name = cat_tr if lang == "tr" else cat_en
    btn = tk.Button(
        cats_frame,
        text=f"{emoji}  {name}",
        font=("Segoe UI", 10),
        fg=FG, bg=BG_BTN,
        activebackground=BG_BTN_HOVER, activeforeground="#ffffff",
        bd=0, padx=10, pady=10, cursor="hand2",
        width=16,
        command=lambda tr=cat_tr, en=cat_en, p=path: on_category_click(tr, en, p),
    )
    btn.grid(row=idx // 4, column=idx % 4, padx=5, pady=5, sticky="nsew")
    buttons.append(btn)

for c in range(4):
    cats_frame.columnconfigure(c, weight=1)

tabs_frame = tk.Frame(root, bg=BG)
tabs_frame.pack(fill="x", padx=20, pady=(4, 0))

tab_buttons = []
tab_defs = [
    (t("show_prices"), lambda: on_tab_click(show_prices_tab, 0)),
    (t("show_stats"),  lambda: on_tab_click(show_stats_tab, 1)),
    (t("show_dist"),   lambda: on_tab_click(show_dist_tab, 2)),
]
for i, (txt, cmd) in enumerate(tab_defs):
    tbtn = tk.Button(
        tabs_frame, text=txt,
        font=("Segoe UI", 9, "bold"),
        fg="#ffffff" if i == 0 else FG,
        bg=ACCENT if i == 0 else BG_CARD,
        activebackground=BG_BTN_HOVER, activeforeground="#ffffff",
        bd=0, padx=16, pady=5, cursor="hand2",
        command=cmd,
    )
    tbtn.pack(side="left", padx=(0, 4))
    tab_buttons.append(tbtn)

log_frame = tk.Frame(root, bg=BG)
log_frame.pack(fill="both", expand=True, padx=20, pady=(6, 6))

log_text = tk.Text(
    log_frame,
    font=("Cascadia Code", 10),
    bg=BG_LOG, fg=FG_LOG,
    insertbackground=FG_LOG,
    selectbackground="#264f78",
    bd=0, padx=12, pady=10,
    wrap="word", state="disabled",
    highlightthickness=1, highlightbackground="#30363d",
)
log_text.pack(side="left", fill="both", expand=True)

scrollbar = ttk.Scrollbar(log_frame, command=log_text.yview)
scrollbar.pack(side="right", fill="y")
log_text.config(yscrollcommand=scrollbar.set)

stats_bar = tk.Frame(root, bg=BG_CARD, pady=8, padx=12)
stats_bar.pack(fill="x", padx=20, pady=(0, 6))

stat_keys = ["count", "min", "max", "avg", "median"]
stat_labels = {}
stat_values = {}

for i, key in enumerate(stat_keys):
    cell = tk.Frame(stats_bar, bg=BG_CARD)
    cell.pack(side="left", expand=True, fill="x")
    lbl = tk.Label(cell, text=t(f"stat_{key}"), font=("Segoe UI", 8), fg=FG_DIM, bg=BG_CARD)
    lbl.pack()
    stat_labels[key] = lbl
    val = tk.Label(cell, text=t("stat_na"), font=("Segoe UI", 12, "bold"), fg=FG_DIM, bg=BG_CARD)
    val.pack()
    stat_values[key] = val
    if i < len(stat_keys) - 1:
        tk.Frame(stats_bar, bg="#30363d", width=1).pack(side="left", fill="y", padx=8, pady=4)

bottom = tk.Frame(root, bg=BG, pady=6)
bottom.pack(fill="x", padx=20)

status_label = tk.Label(
    bottom, text=t("status_ready"),
    font=("Segoe UI", 9), fg=FG_DIM, bg=BG, anchor="w"
)
status_label.pack(side="left")

export_btn = tk.Button(
    bottom, text=t("export"),
    font=("Segoe UI", 9), fg=FG, bg=BG_CARD,
    activebackground=BG_BTN_HOVER, activeforeground=FG,
    bd=0, padx=12, pady=4, cursor="hand2",
    command=on_export
)
export_btn.pack(side="right", padx=(6, 0))

clear_btn = tk.Button(
    bottom, text=t("clear"),
    font=("Segoe UI", 9), fg=FG, bg=BG_CARD,
    activebackground=BG_BTN_HOVER, activeforeground=FG,
    bd=0, padx=12, pady=4, cursor="hand2",
    command=lambda: (log_clear(), clear_stats())
)
clear_btn.pack(side="right")

root.mainloop()
