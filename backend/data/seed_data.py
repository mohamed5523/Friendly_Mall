"""Seed 200 base products + thousands of variations into the mall database."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.mall_database import init_db, get_connection
import random, json
from datetime import datetime, timedelta

CATEGORIES = [
    (1, "غرف النوم", "Bedroom", "🛏️"),
    (2, "غرف الجلوس", "Living Room", "🛋️"),
    (3, "المطبخ", "Kitchen", "🍳"),
    (4, "الأجهزة الكهربائية", "Appliances", "⚡"),
    (5, "الإضاءة", "Lighting", "💡"),
    (6, "الحمام", "Bathroom", "🚿"),
    (7, "التنظيف", "Cleaning", "🧹"),
    (8, "الديكور", "Decor", "🖼️"),
]

COLORS = ["أبيض", "أسود", "رمادي", "بني", "بيج", "أحمر", "أزرق", "أخضر", "فضي", "ذهبي"]
MODIFIERS = ["برو", "ماكس", "بلس", "ستاندرد", "إيليت", "سمارت"]
BRANDS_EXT = ["Premium", "Global", "Local Choice", "TechMaster", "HomeDecor"]

BASE_PRODUCTS = [
    # غرف النوم
    (1,"سرير خشب زان مزدوج",1,"أسرّة",2800,"Cairo Wood","متين وأنيق"),
    (2,"سرير مفرد بمرتبة",1,"أسرّة",1200,"Cairo Wood","مناسب للأطفال"),
    (3,"سرير أطفال بطابقين",1,"أسرّة",3500,"Kids Home","توفير في المساحة"),
    (4,"طقم غرفة نوم كامل 6 قطع",1,"طقم كامل",8500,"Royal",None),
    (5,"خزانة ملابس 4 أبواب",1,"خزائن",3200,"Classic","مرايا مدمجة"),
    (6,"خزانة ملابس 6 أبواب",1,"خزائن",4500,"Classic",None),
    (7,"كومودينو خشب",1,"طاولات",350,"Cairo Wood",None),
    (8,"تسريحة مع مرايا",1,"تسريحات",1800,"Royal",None),
    (9,"مرتبة طبية سبرينج",1,"مراتب",1500,"Comfort","مناسبة للظهر"),
    (10,"مرتبة إسفنج عالي الكثافة",1,"مراتب",900,"Foam Plus",None),
    (11,"وسادة طبية",1,"وسائد",250,"Comfort",None),
    (12,"طقم ملاءات قطن 100%",1,"مفروشات",320,"Cotton House",None),
    (13,"لحاف شتوي مزدوج",1,"مفروشات",550,"Cozy",None),
    (14,"ستارة غرفة نوم 2 قطعة",1,"ستائر",420,"Deco",None),

    # غرف الجلوس
    (15,"كنبة 3 مقاعد قماش",2,"كنبات",4200,"Comfort","وثيرة جداً"),
    (16,"كنبة L شكل",2,"كنبات",6800,"Royal",None),
    (17,"كنبة جلد طبيعي 3+2",2,"كنبات",12000,"Luxury",None),
    (18,"طقم انتريه 7 قطع",2,"طقم كامل",15000,"Royal",None),
    (19,"طاولة سفرة وسط خشب",2,"طاولات",850,"Classic",None),
    (20,"طاولة زاوية",2,"طاولات",450,"Classic",None),
    (21,"رف تلفزيون خشب",2,"أرفف",1200,"Cairo Wood",None),
    (22,"مكتبة خشب 5 رفوف",2,"أرفف",1800,"Cairo Wood",None),
    (23,"بوفيه خشب 3 أبواب",2,"بوافيه",2200,"Royal",None),
    (24,"سجادة برازيلية 3x4",2,"سجاد",1100,"Carpet House",None),
    (25,"سجادة تركي 2x3",2,"سجاد",1800,"Carpet House",None),
    (26,"ستارة جلوس حرير صناعي",2,"ستائر",600,"Deco",None),
    (27,"مرآة حائط كبيرة",2,"ديكور",550,"Deco",None),
    (28,"كرسي استرخاء مع مسند قدم",2,"كراسي",2800,"Comfort",None),

    # المطبخ
    (29,"طقم أطباق 24 قطعة",3,"أطباق",380,"Home Table",None),
    (30,"طقم أطباق بورسليان 12 قطعة",3,"أطباق",550,"Fine China",None),
    (31,"طقم أكواب زجاج 6 قطع",3,"أكواب",95,"Glass House",None),
    (32,"طقم أكواب شاي 12 قطعة",3,"أكواب",145,"Fine China",None),
    (33,"مقلاة تيفال 28 سم",3,"مقالي",420,"Tefal",None),
    (34,"مقلاة جرانيت 30 سم",3,"مقالي",280,"Granite King",None),
    (35,"طقم حلل 7 قطع استانلس",3,"حلل",650,"Steel Plus",None),
    (36,"طقم حلل جرانيت 5 قطع",3,"حلل",480,"Granite King",None),
    (37,"خلاط كهربائي 2 لتر",3,"خلاطات",350,"Braun",None),
    (38,"عصارة كهربائية",3,"عصارات",280,"Philips",None),
    (39,"محضرة طعام متعددة",3,"محضرات",750,"Braun",None),
    (40,"فرن كهربائي 45 لتر",3,"أفران",2200,"Delonghi",None),
    (41,"ميكروويف 25 لتر",3,"ميكروويف",1800,"LG",None),
    (42,"غلاية كهربائية",3,"غلايات",180,"Moulinex",None),
    (43,"ماكينة قهوة أمريكية",3,"ماكينات قهوة",650,"Nescafe",None),
    (44,"ماكينة ايسبريسو",3,"ماكينات قهوة",2800,"Delonghi",None),
    (45,"طاولة مطبخ مع 4 كراسي",3,"طاولات",3200,"Classic",None),
    (46,"رف مطبخ معلق استانلس",3,"أرفف",350,"Steel Plus",None),
    (47,"منظم أدراج مطبخ",3,"تنظيم",85,"Organize",None),
    (48,"طقم سكاكين 5 قطع",3,"أدوات",220,"Sharp Cut",None),
    (49,"لوح تقطيع خشب كبير",3,"أدوات",95,"Wood Chef",None),
    (50,"ميزان مطبخ رقمي",3,"أدوات",120,"Kitchen Pro",None),

    # الأجهزة الكهربائية
    (51,"ثلاجة نوفروست 16 قدم",4,"ثلاجات",12500,"Samsung","ضامن 3 سنين"),
    (52,"ثلاجة نوفروست 14 قدم",4,"ثلاجات",9800,"LG",None),
    (53,"ثلاجة نوفروست 20 قدم",4,"ثلاجات",15500,"Toshiba",None),
    (54,"ثلاجة ميني بار",4,"ثلاجات",2200,"Sharp",None),
    (55,"غسالة أتوماتيك 7 كيلو",4,"غسالات",8500,"LG","توفير مياه"),
    (56,"غسالة أتوماتيك 9 كيلو",4,"غسالات",11000,"Samsung",None),
    (57,"غسالة نص أتوماتيك",4,"غسالات",3200,"White Whale",None),
    (58,"تلفزيون سمارت 43 بوصة",4,"تلفزيونات",8500,"Samsung","4K UHD"),
    (59,"تلفزيون سمارت 55 بوصة",4,"تلفزيونات",13500,"LG","OLED"),
    (60,"تلفزيون سمارت 65 بوصة",4,"تلفزيونات",22000,"Sony",None),
    (61,"مكيف سبليت 1.5 حصان",4,"مكيفات",8500,"Carrier","موفر طاقة"),
    (62,"مكيف سبليت 2 حصان",4,"مكيفات",11000,"Midea",None),
    (63,"مكيف شباك 1 حصان",4,"مكيفات",4500,"Unionaire",None),
    (64,"مروحة أرضية 18 بوصة",4,"مراوح",450,"Tornado",None),
    (65,"مروحة سقف 56 بوصة",4,"مراوح",850,"Cairo Fan","هادية"),
    (66,"مروحة برج",4,"مراوح",680,"Philips",None),
    (67,"سخان كهربائي 80 لتر",4,"سخانات",3200,"Ariston",None),
    (68,"سخان شمسي 200 لتر",4,"سخانات",5500,"Solar Tech",None),
    (69,"بوتاجاز 4 شعلة فرن",4,"بوتاجازات",4800,"Zanussi",None),
    (70,"بوتاجاز 5 شعلة ستانلس",4,"بوتاجازات",6500,"Beko",None),
    (71,"مكنسة كهربائية روبوت",4,"مكانس",3800,"Xiaomi",None),
    (72,"مكنسة كهربائية لاسلكية",4,"مكانس",1800,"Philips",None),
    (73,"مكيف هواء نقال",4,"مكيفات",6500,"Midea",None),
    (74,"جهاز تنقية هواء",4,"تنقية هواء",2200,"Philips",None),
    (75,"جهاز ترطيب هواء",4,"ترطيب هواء",450,"Deerma",None),

    # الإضاءة
    (76,"ثريا كريستال كبيرة",5,"ثريات",2800,"Crystal Light",None),
    (77,"ثريا مودرن صغيرة",5,"ثريات",1200,"Modern Light",None),
    (78,"لمبة LED 12 واط",5,"لمبات",35,"Philips",None),
    (79,"لمبة LED 20 واط",5,"لمبات",55,"Osram",None),
    (80,"شريط LED ملون 5 متر",5,"شرائط LED",180,"RGB Strip",None),
    (81,"سبوت لايت داخلي",5,"سبوت",45,"Spark",None),
    (82,"باكيت إضاءة خارجية",5,"خارجي",220,"Outdoor Pro",None),
    (83,"مصباح طاولة مكتب",5,"مصابيح",180,"Study Light",None),
    (84,"مصباح حائط ديكور",5,"مصابيح",320,"Deco",None),
    (85,"إضاءة ذكية واي فاي",5,"ذكية",250,"Xiaomi",None),

    # الحمام
    (86,"طقم منشفة قطن 6 قطع",6,"مناشف",320,"Cotton House",None),
    (87,"منشفة كبيرة قطن تركي",6,"مناشف",85,"Turkish Bath",None),
    (88,"طقم شاور 5 قطع",6,"شاور",680,"Grohe",None),
    (89,"مرآة حمام مضيئة",6,"مرايا",450,"Bath Mirror",None),
    (90,"خزانة حمام مع مرآة",6,"خزائن",1100,"Bath Storage",None),
    (91,"سجادة حمام مطاط",6,"سجاد",65,"Bath Rug",None),
    (92,"حامل مناشف أرضي",6,"حوامل",220,"Steel Bath",None),
    (93,"ديسبنسر صابون أتوماتيك",6,"إكسسوار",180,"Auto Soap",None),

    # التنظيف
    (94,"مكنسة كهربائية كيس",7,"مكانس",1200,"Electrolux",None),
    (95,"ممسحة بخارية",7,"ممسحات",650,"Steam Clean",None),
    (96,"جرادل ومقشة",7,"أدوات",85,"Clean Pro",None),
    (97,"منظف متعدد الأغراض",7,"منظفات",45,"Clean Pro",None),
    (98,"مبيد حشرات كهربائي",7,"مبيدات",120,"Raid",None),
    (99,"لوح غسيل ملابس",7,"أدوات",35,"Wash Board",None),
    (100,"منشر ملابس قابل للطي",7,"منشرات",180,"Laundry",None),

    # الديكور
    (101,"إطار صور خشب 30x40",8,"إطارات",65,"Frame House",None),
    (102,"لوحة فنية مودرن",8,"لوحات",350,"Art Home",None),
    (103,"نبتة صناعية كبيرة",8,"نباتات",180,"Green Deco",None),
    (104,"إناء ورد سيراميك",8,"أوعية",85,"Ceramic Art",None),
    (105,"ساعة حائط خشب كبيرة",8,"ساعات",220,"Time Deco",None),
    (106,"ساعة طاولة كلاسيك",8,"ساعات",150,"Classic Time",None),
    (107,"شمعة ديكور عطرية",8,"شموع",55,"Aroma",None),
    (108,"سلة تخزين قش",8,"سلال",120,"Wicker",None),
    (109,"سرير ديوان أرضي مع خزين",1,"ديوان",4500,"Classic",None),
    (110,"مرتبة فوم مولتي لاير 180",1,"مراتب",2200,"Comfort Plus",None),
    (111,"خزانة ملابس زاوية",1,"خزائن",5200,"Space Saver",None),
    (112,"ستارة بلاك أوت 2 قطعة",1,"ستائر",380,"Black Out",None),
    (113,"طقم أدوات مطبخ 12 قطعة",3,"أدوات",280,"Kitchen Pro",None),
    (114,"توستر كهربائي",3,"توستر",220,"Black+Decker",None),
    (115,"شواية كهربائية",3,"شوايات",550,"Tefal",None),
    (116,"مكنسة مطبخ يدوية",3,"تنظيف",45,"Mini Clean",None),
    (117,"منظم بهارات دوار",3,"تنظيم",95,"Spice Rack",None),
    (118,"سماعات بلوتوث",4,"إلكترونيات",450,"JBL",None),
    (119,"شحن لاسلكي",4,"إلكترونيات",180,"Xiaomi",None),
    (120,"كابل HDMI 3 متر",4,"إكسسوار",45,"AmazonBasics",None),
    (121,"مقسم USB Hub",4,"إكسسوار",120,"Orico",None),
    (122,"سوكيت متعدد المنافذ",4,"إكسسوار",85,"Philips",None),
    (123,"طاولة تلفزيون مودرن",2,"طاولات",1500,"Modern Home",None),
    (124,"كرسي مكتب دوار",2,"كراسي",1800,"Office Pro",None),
    (125,"أريكة كودوي 2 مقعد",2,"كنبات",2800,"Comfort",None),
    (126,"رف جداري عائم",2,"أرفف",220,"Float Shelf",None),
    (127,"طاولة طعام 6 كراسي",2,"طاولات",5500,"Classic",None),
    (128,"درج تخزين تحت السرير",1,"تخزين",350,"Under Bed",None),
    (129,"حقيبة تخزين ملابس",1,"تخزين",65,"Storage",None),
    (130,"واقي مرتبة ضد الماء",1,"مراتب",180,"Protect",None),
    (131,"لحاف صيفي مزدوج",1,"مفروشات",380,"Cool Sleep",None),
    (132,"مخدة ظهر",1,"وسائد",120,"Back Support",None),
    (133,"طقم غرفة أطفال كامل",1,"طقم كامل",9500,"Kids Room",None),
    (134,"سرير أطفال قضبان",1,"أسرّة",2200,"Baby Safe",None),
    (135,"تشيز لونج جلوس",2,"كنبات",3500,"Relax",None),
    (136,"طاولة قهوة زجاج",2,"طاولات",680,"Glass Home",None),
    (137,"سجادة شاغي ناعمة",2,"سجاد",950,"Shaggy",None),
    (138,"تابلوه ثلاث قطع",8,"لوحات",450,"Art Home",None),
    (139,"هانجر ملابس خشب كبير",1,"تخزين",280,"Wooden Hanger",None),
    (140,"حامل ملابس قابل للتمديد",7,"منشرات",220,"Extendable",None),
    (141,"صندوق تخزين بلاستيك",7,"تخزين",95,"Store Box",None),
    (142,"علاقة باب 10 خطافات",1,"تخزين",45,"Hook Set",None),
    (143,"مضخة فراغ للملابس",1,"تخزين",120,"Vacuum Bag",None),
    (144,"ترموس شاي 2 لتر",3,"ترموس",180,"Vacuum Flask",None),
    (145,"طقم فناجين قهوة عربية",3,"أكواب",220,"Arabic Coffee",None),
    (146,"إبريق شاي كهربائي زجاج",3,"غلايات",350,"Glass Kettle",None),
    (147,"صانع الفشار كهربائي",3,"أجهزة ترفيهية",320,"Pop Corn",None),
    (148,"آلة صنع العصير البارد",3,"عصارات",850,"Cold Press",None),
    (149,"خبازة كهربائية",3,"خبازات",1200,"Bread Maker",None),
    (150,"ميكسر يدوي",3,"خلاطات",280,"Hand Mixer",None),
    (151,"وعاء حفظ طعام كبير",3,"أوعية",45,"Lock Tight",None),
    (152,"طقم برطمانات زجاج 6 قطع",3,"أوعية",180,"Glass Store",None),
    (153,"مغسلة غسيل خضار",3,"أدوات",85,"Wash Bowl",None),
    (154,"مصفى معكرونة استانلس",3,"أدوات",55,"Steel Drain",None),
    (155,"مطرقة اللحم",3,"أدوات",35,"Meat Tender",None),
    (156,"باكيت طعام الدواجن",3,"أدوات",25,"Poultry Kit",None),
    (157,"شبكة سلامة مطبخ للأطفال",3,"سلامة",65,"Safety Net",None),
    (158,"قفل أدراج أطفال",3,"سلامة",45,"Child Lock",None),
    (159,"زبالة مطبخ بغطاء",3,"تنظيم",75,"Trash Can",None),
    (160,"حامل ورق المطبخ",3,"تنظيم",35,"Paper Hold",None),
    (161,"ثلاجة ديب فريزر صندوق",4,"ثلاجات",6500,"White Whale",None),
    (162,"مروحة يدوية USB",4,"مراوح",65,"USB Fan",None),
    (163,"بطانية كهربائية",4,"تدفئة",450,"Electric Warm",None),
    (164,"دفاية نفط",4,"تدفئة",850,"Oil Heater",None),
    (165,"مدفأة كهربائية",4,"تدفئة",1200,"Fire Place",None),
    (166,"كاشف غاز",4,"سلامة",120,"Gas Detector",None),
    (167,"كاشف دخان",4,"سلامة",95,"Smoke Alarm",None),
    (168,"طفاية حريق منزلية",4,"سلامة",180,"Fire Guard",None),
    (169,"UPS احتياطي كهرباء",4,"UPS",850,"APC",None),
    (170,"مولد كهرباء صغير",4,"مولدات",12000,"Honda",None),
    (171,"شاشة كمبيوتر 24 بوصة",4,"شاشات",3500,"Samsung",None),
    (172,"طابعة منزلية",4,"طابعات",2200,"HP",None),
    (173,"راوتر واي فاي",4,"شبكات",450,"TP-Link",None),
    (174,"سماعة بلوتوث محمولة",4,"إلكترونيات",380,"JBL",None),
    (175,"شاحن سيارة",4,"إكسسوار",65,"Car Charge",None),
    (176,"مصباح طوارئ LED",5,"طوارئ",85,"Emergency",None),
    (177,"حزام إضاءة سقف",5,"شرائط LED",220,"Ceiling LED",None),
    (178,"ضوء ليلي حساس حركة",5,"حساسات",75,"Motion Night",None),
    (179,"أباجورة طاولة",5,"أباجورات",280,"Table Lamp",None),
    (180,"مصباح حديقة خارجي",5,"خارجي",180,"Garden Light",None),
    (181,"صابون سائل حمام",6,"منظفات",35,"Dove",None),
    (182,"شامبو فاخر",6,"منظفات",75,"Pantene",None),
    (183,"بشكير حمام فندقي",6,"مناشف",120,"Hotel Grade",None),
    (184,"صينية حمام بلاستيك",6,"إكسسوار",25,"Bath Tray",None),
    (185,"طقم إكسسوار حمام 5 قطع",6,"إكسسوار",320,"Bath Set",None),
    (186,"حصيرة حمام سيليكون",6,"سجاد",95,"Silicon Mat",None),
    (187,"ستارة دش بلاستيك",6,"ستائر",65,"Shower Curtain",None),
    (188,"جهاز إزالة الشعر بالليزر",6,"العناية",850,"Laser Care",None),
    (189,"مجفف شعر كهربائي",6,"العناية",350,"Philips",None),
    (190,"ماكينة حلاقة",6,"العناية",280,"Braun",None),
    (191,"مكنسة رذاذ ومسح",7,"مكانس",380,"Spray Mop",None),
    (192,"سلة غسيل كبيرة",7,"سلال",85,"Laundry Basket",None),
    (193,"علاقة ملابس للباب",7,"منشرات",35,"Door Hang",None),
    (194,"بخاخ تنظيف متعدد",7,"منظفات",25,"Multi Spray",None),
    (195,"جهاز تلميع أرضيات",7,"أجهزة",1200,"Floor Polish",None),
    (196,"فرشاة مرحاض مع حامل",6,"إكسسوار",45,"Toilet Brush",None),
    (197,"هلال ديكور رمضاني",8,"ديكور موسمي",95,"Ramadan Deco",None),
    (198,"شجرة كريسماس",8,"ديكور موسمي",450,"Xmas Tree",None),
    (199,"تابلوه آيات قرآنية",8,"لوحات",280,"Islamic Art",None),
    (200,"بورتريه عائلي فارغ",8,"إطارات",180,"Family Frame",None),
]

def generate_variations():
    """Generate thousands of products by combining base products with variations."""
    new_products = []
    pid = 1
    for p in BASE_PRODUCTS:
        # Base product: (1,"سرير...", 1, "أسرّة", 2800, "Brand", "desc")
        _, base_name, cat_id, sub_cat, base_price, base_brand, base_desc = p
        
        # Add the original product
        new_products.append({
            "id": pid,
            "name_ar": base_name,
            "category_id": cat_id,
            "sub_category": sub_cat,
            "price": base_price,
            "brand": base_brand,
            "description_ar": base_desc,
            "color": random.choice(COLORS),
            "stock_count": random.randint(5, 100)
        })
        pid += 1

        # Generate 5-10 variations for each base product
        num_variations = random.randint(5, 12)
        for _ in range(num_variations):
            color = random.choice(COLORS)
            modifier = random.choice(MODIFIERS)
            brand = random.choice([base_brand] + BRANDS_EXT)
            
            # Create variation name
            var_name = f"{base_name} {modifier} - لون {color}"
            
            # Slightly adjust price
            price_mult = random.uniform(0.8, 1.5)
            new_price = round(base_price * price_mult, -1)  # Round to nearest 10
            
            new_products.append({
                "id": pid,
                "name_ar": var_name,
                "category_id": cat_id,
                "sub_category": sub_cat,
                "price": new_price,
                "brand": brand,
                "description_ar": f"{base_desc or 'منتج مميز'} - نسخة {modifier} بلون {color} رائع",
                "color": color,
                "stock_count": random.randint(0, 150)
            })
            pid += 1

    return new_products

def seed():
    print("Starting database seed process...")
    init_db()
    with get_connection() as conn:
        print("Inserting categories and users...")
        # Insert categories
        for cat in CATEGORIES:
            conn.execute(
                "INSERT OR IGNORE INTO categories (id, name_ar, name_en, icon) VALUES (?,?,?,?)",
                cat
            )

        # Insert dummy users
        users = [
            ("mallrag@cust.com", "password123", "customer"),
            ("mallrag@man.com", "password123", "manager")
        ]
        for email, password, role in users:
            conn.execute(
                "INSERT OR IGNORE INTO users (email, password, role) VALUES (?,?,?)",
                (email, password, role)
            )
            
        print("Generating product variations...")
        products_data = generate_variations()
        
        print(f"Inserting {len(products_data)} products into the database...")
        # Insert products
        # Using executemany for speed
        product_rows = [
            (
                p["id"], p["name_ar"], p["category_id"], p["sub_category"], 
                p["price"], p["stock_count"], p["brand"], p["description_ar"], p["color"]
            ) for p in products_data
        ]
        conn.executemany(
            """INSERT OR IGNORE INTO products
               (id, name_ar, category_id, sub_category, price, stock_count, brand, description_ar, color)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            product_rows
        )

        print("Generating 25,000 sales records (this may take a few seconds)...")
        # Seed random sales history
        import datetime as dt
        today = dt.date.today()
        
        # Prepare sales history efficiently
        sales_rows = []
        for _ in range(25000):
            p = random.choice(products_data)
            days_ago = random.randint(0, 365) # Up to a year of data
            sale_date = (today - dt.timedelta(days=days_ago)).isoformat()
            qty = random.randint(1, 10)
            price = p["price"]
            revenue = qty * price
            
            sales_rows.append(
                (p["id"], p["name_ar"], p["category_id"], qty, price, revenue, sale_date)
            )

        # Insert in chunks of 5000 to keep it manageable
        chunk_size = 5000
        for i in range(0, len(sales_rows), chunk_size):
            chunk = sales_rows[i:i+chunk_size]
            conn.executemany(
                """INSERT INTO sales_history
                   (product_id, product_name, category_id, quantity_sold, unit_price, revenue, sale_date)
                   VALUES (?,?,?,?,?,?,?)""",
                chunk
            )

        print("Generating 2,000 merchant orders (wholesale)...")
        merchants = ["مؤسسة الحمد", "أولاد رجب للتجارة", "شركات النور", "الشركة الهندسية", "تجارة بلا حدود"]
        merchant_rows = []
        for _ in range(2000):
            p = random.choice(products_data)
            days_ago = random.randint(0, 365)
            order_date = (today - dt.timedelta(days=days_ago)).isoformat()
            qty = random.randint(50, 500)  # bulk quantities
            price = p["price"] * 0.8  # 20% discount for wholesale
            total_value = qty * price
            merchant = random.choice(merchants)
            
            merchant_rows.append(
                (merchant, p["id"], p["name_ar"], qty, price, total_value, order_date)
            )
            
        for i in range(0, len(merchant_rows), chunk_size):
            chunk = merchant_rows[i:i+chunk_size]
            conn.executemany(
                """INSERT INTO merchant_orders
                   (merchant_name, product_id, product_name, quantity, unit_price, total_value, order_date)
                   VALUES (?,?,?,?,?,?,?)""",
                chunk
            )

    print(f"Done! Seeded {len(products_data)} products, 25,000 sales records, and 2,000 merchant orders successfully.")

if __name__ == "__main__":
    seed()
