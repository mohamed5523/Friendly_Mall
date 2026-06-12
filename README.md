## كيفية تشغيل نظام لمعي جراند مول

### المتطلبات
- Python 3.11+
- Node.js 18+
- OpenAI API Key

---

### الإعداد الأول

**1. ضع مفتاح OpenAI في ملف `.env`:**
```
OPENAI_API_KEY=sk-proj-xxxxxxx
LLM_MODEL=gpt-4o
MALL_NAME=لمعي جراند مول
MCP_BASE_URL=http://localhost:8001
```

**2. تهيئة قاعدة البيانات (مرة واحدة فقط):**
```bash
cd backend
python data/seed_data.py
```

---

### التشغيل اليومي

**ترمينال 1 — Backend (FastAPI):**
```bash
cd backend
python run.py
# يعمل على: http://localhost:8000
```

**ترمينال 2 — MCP Server:**
```bash
cd backend/MCP
python main.py
# يعمل على: http://localhost:8001
```

**ترمينال 3 — Frontend:**
```bash
cd frontend
npm run dev
# يعمل على: http://localhost:8080
```

---

### روابط مهمة
- 🏪 **الواجهة الرئيسية:** http://localhost:8080
- 📡 **Backend API:** http://localhost:8000
- 📖 **Swagger Docs:** http://localhost:8000/docs
- 🔌 **MCP Server:** http://localhost:8001

---

### الأدوات المتاحة (15 أداة)

#### للعميل (Customer)
| الأداة | الوصف |
|--------|--------|
| `search_products_tool` | البحث عن منتج |
| `check_product_price` | سعر المنتج |
| `check_product_stock` | هل المنتج متاح؟ |
| `get_products_by_category_tool` | عرض فئة كاملة |
| `reserve_product` | حجز منتج |
| `buy_product` | شراء منتج |
| `check_order_status` | متابعة الطلب |

#### للمدير (Manager)
| الأداة | الوصف |
|--------|--------|
| `get_sales_report_tool` | تقرير المبيعات |
| `get_revenue_analysis` | تحليل الإيرادات |
| `get_top_selling_products` | أكثر المنتجات مبيعاً |
| `predict_product_demand` | توقع الطلب (LLM) |
| `get_low_stock_alert` | تنبيه المخزون |
| `get_product_correlation_insights` | ارتباط المنتجات |
| `get_manager_insights` | رؤى شاملة (LLM) |
| `get_account_summary_tool` | ملخص الحسابات |

---

### البنية
```
Mall_Project/MedRag/
├── backend/
│   ├── data/
│   │   ├── mall_database.py   # قاعدة بيانات SQLite
│   │   ├── seed_data.py       # بيانات وهمية 200 منتج
│   │   └── mall.db            # ملف قاعدة البيانات
│   ├── MCP/
│   │   └── mall_server.py     # 15 أداة MCP
│   ├── app/
│   │   ├── core/              # State, Router, QA, Memory
│   │   ├── api/chat.py        # Chat endpoint
│   │   └── services/          # Mall workflow
│   └── run.py
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── RoleSelector.tsx
│       │   └── ChatPage.tsx
│       └── index.css
└── .env
```
