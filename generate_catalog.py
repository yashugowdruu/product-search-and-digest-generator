import html
import json
import os
import re

# Original 8 products (kept intact so existing mechanical keyboard test cases TC01-TC08 pass identically)
BASE_LISTINGS = {
    "TechKart": [
        ("Logitech G Pro Mechanical Keyboard", "Compact tenkeyless mechanical keyboard with GX Blue switches.", 5700, 4.5, 320, "In Stock", "https://techkart.example.com/logitech-g-pro"),
        ("Redragon K552 Mechanical Keyboard", "Budget RGB mechanical keyboard with red switches.", 4200, 4.1, 145, "In Stock", "https://techkart.example.com/redragon-k552"),
        ("Sony WH-1000XM5 Wireless Headphones", "Industry-leading noise cancelling over-ear wireless headphones with 30-hour battery.", 26990, 4.7, 540, "In Stock", "https://techkart.example.com/sony-xm5"),
        ("HP Victus Gaming Laptop", "15.6-inch FHD gaming laptop with Ryzen 5, 16GB RAM, and RTX 3050 GPU.", 64990, 4.4, 195, "In Stock", "https://techkart.example.com/hp-victus"),
        ("Logitech MX Master 3S Wireless Mouse", "Ergonomic wireless productivity mouse with quiet clicks and 8K DPI sensor.", 8990, 4.8, 410, "In Stock", "https://techkart.example.com/mx-master-3s"),
    ],
    "MegaStore": [
        ("Logitech G Pro Mechanical Keyboard", "Pro-grade mechanical keyboard for esports and typing.", 6500, 4.2, 210, "In Stock", "https://megastore.example.com/logitech-g-pro"),
        ("Redragon K552 Mechanical Keyboard", "Compact mechanical keyboard with metal chassis.", 3900, 3.8, 88, "Out of Stock", "https://megastore.example.com/redragon-k552"),
        ("Sony WH-1000XM5 Wireless Headphones", "Premium ANC wireless headphones with multipoint Bluetooth connectivity.", 28500, 4.6, 310, "In Stock", "https://megastore.example.com/sony-xm5"),
        ("Lenovo IdeaPad Slim 5 Laptop", "Lightweight 14-inch student laptop with Intel i5, 16GB RAM, and 512GB SSD.", 54990, 4.3, 260, "In Stock", "https://megastore.example.com/ideapad-slim-5"),
        ("Razer DeathAdder Essential Gaming Mouse", "Wired optical gaming mouse with 6400 DPI sensor and ergonomic grip.", 1499, 4.2, 620, "In Stock", "https://megastore.example.com/deathadder"),
    ],
    "ByteBazaar": [
        ("Logitech G Pro Mechanical Keyboard", "Fast delivery mechanical keyboard with detachable cable.", 5950, 4.7, 410, "In Stock", "https://bytebazaar.example.com/logitech-g-pro"),
        ("JBL Tune 760NC Wireless Headphones", "Foldable active noise cancelling headphones with pure bass sound.", 4999, 4.3, 390, "In Stock", "https://bytebazaar.example.com/jbl-760nc"),
        ("HP Victus Gaming Laptop", "High-refresh gaming laptop with Ryzen 5 processor and dual-fan cooling.", 62500, 4.6, 150, "In Stock", "https://bytebazaar.example.com/hp-victus"),
        ("Logitech MX Master 3S Wireless Mouse", "Flagship wireless mouse with MagSpeed scroll wheel and USB-C charging.", 8490, 4.7, 285, "Out of Stock", "https://bytebazaar.example.com/mx-master-3s"),
    ],
    "GadgetHub": [
        ("Sony WH-1000XM5 Wireless Headphones", "Lightweight noise cancelling wireless headphones with clear call quality.", 25990, 4.5, 180, "In Stock", "https://gadgethub.example.com/sony-xm5"),
        ("Lenovo IdeaPad Slim 5 Laptop", "Thin metal-body laptop with backlit keys, 16GB RAM, 512GB SSD, and fast charge.", 52990, 4.5, 340, "In Stock", "https://gadgethub.example.com/ideapad-slim-5"),
        ("Razer DeathAdder Essential Gaming Mouse", "Durable gaming mouse with 5 programmable buttons.", 1350, 4.4, 510, "In Stock", "https://gadgethub.example.com/deathadder"),
        ("JBL Tune 760NC Wireless Headphones", "Budget wireless ANC headphones with 35-hour playback time.", 4799, 4.1, 215, "In Stock", "https://gadgethub.example.com/jbl-760nc"),
    ],
    "ShopSphere": [],
    "ValueMart": [],
}

# 105 additional general products across 11 everyday categories (min 2-3 comparable websites each)
GENERAL_PRODUCTS = [
    # 1. Smartphones (10)
    ("Apple iPhone 15 128GB Smartphone", "6.1-inch Super Retina XDR display smartphone with A16 Bionic chip and 48MP camera.", 65999, 4.7, 1420, ["TechKart", "MegaStore", "ShopSphere"]),
    ("Samsung Galaxy S24 5G Smartphone", "Compact flagship Android smartphone with Dynamic AMOLED 2X display and AI camera.", 62999, 4.6, 980, ["TechKart", "ByteBazaar", "ShopSphere"]),
    ("OnePlus 12R 5G Smartphone", "Fast-charging 5G smartphone with Snapdragon 8 Gen 2 processor and 120Hz AMOLED screen.", 39999, 4.5, 1150, ["TechKart", "GadgetHub", "ShopSphere"]),
    ("Google Pixel 8a 5G Smartphone", "Clean Android smartphone with Tensor G3 chip and industry-leading computational photography.", 44999, 4.5, 640, ["ByteBazaar", "GadgetHub", "ShopSphere"]),
    ("Xiaomi Redmi Note 13 Pro Smartphone", "Mid-range 5G phone with 200MP OIS camera, AMOLED display, and 67W turbo charging.", 23999, 4.3, 1890, ["MegaStore", "ValueMart", "GadgetHub"]),
    ("Motorola Edge 50 Fusion Smartphone", "Curved pOLED display 5G smartphone with IP68 water resistance and vegan leather back.", 22999, 4.4, 730, ["TechKart", "ValueMart", "ShopSphere"]),
    ("Nothing Phone 2a 5G Smartphone", "Unique Glyph interface smartphone with MediaTek Dimensity 7200 Pro and clean OS.", 23999, 4.4, 860, ["ByteBazaar", "GadgetHub"]),
    ("Realme Narzo 70 Pro Smartphone", "Budget 5G smartphone with Sony IMX890 OIS sensor and 120Hz bright AMOLED screen.", 18999, 4.2, 920, ["MegaStore", "ValueMart"]),
    ("Vivo V30 5G Smartphone", "Slim portrait camera smartphone with Aura Light flash and 5000mAh battery.", 31999, 4.3, 510, ["TechKart", "ShopSphere"]),
    ("iQOO Neo 9 Pro Gaming Smartphone", "Performance smartphone with Snapdragon 8 Gen 2, 144Hz display, and 120W fast charge.", 35999, 4.6, 840, ["ByteBazaar", "GadgetHub"]),

    # 2. Laptops & Tablets (10)
    ("Apple MacBook Air M2 Laptop", "Ultra-thin 13.6-inch Liquid Retina laptop with Apple M2 chip and 18-hour battery.", 89990, 4.8, 1120, ["TechKart", "ByteBazaar", "MegaStore"]),
    ("Dell Inspiron 15 Thin Laptop", "15.6-inch Full HD work laptop with Intel Core i5 13th Gen, 16GB RAM, and 512GB SSD.", 53990, 4.3, 470, ["TechKart", "MegaStore", "ValueMart"]),
    ("Asus Vivobook 16 OLED Laptop", "Creator laptop with vibrant 16-inch OLED display, Ryzen 7 processor, and sleek chassis.", 67990, 4.5, 390, ["ByteBazaar", "TechKart"]),
    ("Acer Aspire 5 Everyday Laptop", "Reliable student and office laptop with Intel i5 processor, aluminum cover, and WiFi 6.", 46990, 4.2, 520, ["MegaStore", "ValueMart"]),
    ("MSI Thin 15 Gaming Laptop", "Lightweight gaming laptop with Intel i7, RTX 4050 graphics, and 144Hz IPS panel.", 76990, 4.4, 280, ["TechKart", "ByteBazaar"]),
    ("Apple iPad 10th Gen Tablet", "10.9-inch Liquid Retina display tablet with A14 Bionic chip and USB-C support.", 33900, 4.7, 940, ["TechKart", "GadgetHub", "ShopSphere"]),
    ("Samsung Galaxy Tab S9 FE Tablet", "Water-resistant Android tablet with included S Pen stylus and 90Hz vivid display.", 34999, 4.5, 610, ["MegaStore", "ByteBazaar", "ShopSphere"]),
    ("Xiaomi Pad 6 Android Tablet", "Productivity tablet with 2.8K 144Hz display, Snapdragon 870, and quad Dolby speakers.", 26999, 4.6, 890, ["GadgetHub", "ValueMart"]),
    ("Lenovo Tab M11 Student Tablet", "11-inch FHD entertainment and study tablet with stylus support and Dolby Atmos.", 16999, 4.2, 430, ["MegaStore", "ValueMart"]),
    ("OnePlus Pad Go WiFi Tablet", "2.4K ReadFit eye-care screen tablet with 8000mAh battery and 33W SUPERVOOC charging.", 19999, 4.4, 570, ["ByteBazaar", "GadgetHub"]),

    # 3. Audio: Earbuds, Headphones & Speakers (10)
    ("Apple AirPods Pro 2nd Gen Earbuds", "Active noise cancelling wireless earbuds with H2 chip, spatial audio, and MagSafe case.", 22990, 4.8, 1650, ["TechKart", "GadgetHub", "ShopSphere"]),
    ("Samsung Galaxy Buds2 Pro Earbuds", "24-bit Hi-Fi wireless earbuds with intelligent ANC and IPX7 water resistance.", 11999, 4.5, 780, ["MegaStore", "GadgetHub", "ByteBazaar"]),
    ("OnePlus Buds 3 Wireless Earbuds", "Dual dynamic driver TWS earbuds with 49dB adaptive noise cancellation and sliding volume.", 5499, 4.5, 1340, ["TechKart", "GadgetHub", "ValueMart"]),
    ("boAt Airdopes 141 Bluetooth Earbuds", "Budget true wireless earbuds with 42-hour playback, ENx mic, and ASAP fast charge.", 1299, 4.1, 4520, ["MegaStore", "ValueMart", "ShopSphere"]),
    ("Sennheiser Accentum Wireless Headphones", "Audiophile over-ear Bluetooth headphones with 50-hour battery and hybrid ANC.", 12990, 4.6, 340, ["TechKart", "ByteBazaar"]),
    ("Marshall Major IV Bluetooth Headphones", "Iconic on-ear wireless headphones with 80-hour playtime and wireless charging.", 11999, 4.6, 620, ["GadgetHub", "ShopSphere"]),
    ("JBL Flip 6 Portable Bluetooth Speaker", "Waterproof IP67 portable party speaker with bold JBL Original Pro Sound.", 9999, 4.6, 1210, ["TechKart", "MegaStore", "ShopSphere"]),
    ("Sony SRS-XB100 Compact Speaker", "Ultra-portable waterproof Bluetooth speaker with extra bass and 16-hour battery.", 3990, 4.4, 670, ["GadgetHub", "ValueMart"]),
    ("Bose SoundLink Flex Bluetooth Speaker", "Rugged outdoor wireless speaker with PositionIQ audio optimization and crisp vocals.", 14900, 4.7, 530, ["TechKart", "ShopSphere"]),
    ("Marshall Emberton II Portable Speaker", "Compact vintage-style Bluetooth speaker with 360-degree True Stereophonic sound.", 15999, 4.7, 410, ["ByteBazaar", "GadgetHub"]),

    # 4. Smartwatches & Wearables (8)
    ("Apple Watch Series 9 Smartwatch", "Bright Always-On Retina smartwatch with S9 SiP, ECG, blood oxygen, and crash detection.", 40999, 4.8, 870, ["TechKart", "GadgetHub", "ShopSphere"]),
    ("Samsung Galaxy Watch 6 Smartwatch", "Sapphire crystal AMOLED smartwatch with body composition analysis and sleep coaching.", 24999, 4.5, 620, ["MegaStore", "GadgetHub", "ShopSphere"]),
    ("Garmin Forerunner 55 GPS Watch", "Lightweight running smartwatch with built-in GPS, pace guidance, and 2-week battery.", 18990, 4.6, 380, ["TechKart", "ShopSphere"]),
    ("Amazfit GTR 4 Fitness Smartwatch", "Dual-band GPS sports watch with 150 workout modes, Bluetooth calling, and 14-day battery.", 14999, 4.4, 540, ["ByteBazaar", "GadgetHub"]),
    ("Noise ColorFit Pro 5 Smartwatch", "1.85-inch AMOLED Bluetooth calling smartwatch with SOS technology and custom dials.", 3499, 4.2, 2310, ["MegaStore", "ValueMart", "ShopSphere"]),
    ("Fire-Boltt Phoenix AMOLED Smartwatch", "Round dial budget smartwatch with Bluetooth calling, SpO2 monitoring, and metal body.", 1999, 4.0, 3180, ["ValueMart", "GadgetHub"]),
    ("Fitbit Charge 6 Fitness Tracker", "Slim health and fitness band with Google Maps, heart rate tracking, and 7-day battery.", 13999, 4.4, 490, ["TechKart", "ShopSphere"]),
    ("Mi Smart Band 8 Fitness Band", "60Hz AMOLED fitness tracker with quick-release straps and 16-day battery life.", 3999, 4.3, 1450, ["GadgetHub", "ValueMart"]),

    # 5. Monitors, Storage & Computer Peripherals (12)
    ("LG UltraGear 27 Inch Gaming Monitor", "27-inch QHD 144Hz IPS gaming monitor with 1ms response time and FreeSync Premium.", 22999, 4.6, 560, ["TechKart", "ByteBazaar", "MegaStore"]),
    ("Dell S2421HN 24 Inch IPS Monitor", "Full HD thin-bezel home office monitor with ComfortView flicker-free screen.", 10499, 4.5, 740, ["TechKart", "MegaStore"]),
    ("BenQ GW2480 Eye Care Monitor", "24-inch IPS LED monitor with Brightness Intelligence sensor and built-in speakers.", 9990, 4.5, 1120, ["ByteBazaar", "ValueMart"]),
    ("Samsung Odyssey G3 144Hz Monitor", "24-inch borderless gaming monitor with height-adjustable ergonomic stand.", 12999, 4.4, 430, ["TechKart", "ByteBazaar"]),
    ("Samsung T7 1TB Portable SSD", "Ultra-fast USB 3.2 Gen 2 external solid state drive with 1050MB/s read speed.", 8499, 4.7, 1890, ["TechKart", "ByteBazaar", "GadgetHub"]),
    ("SanDisk Extreme 1TB External SSD", "Rugged IP65 water- and dust-resistant portable NVMe SSD for creators and travelers.", 8999, 4.6, 1420, ["ByteBazaar", "GadgetHub", "MegaStore"]),
    ("WD My Passport 2TB External Hard Drive", "Compact USB 3.0 portable HDD with automatic backup software and password protection.", 6199, 4.4, 2450, ["MegaStore", "ValueMart", "ByteBazaar"]),
    ("Crucial P3 Plus 1TB NVMe SSD", "PCIe Gen4 M.2 internal solid state drive with up to 5000MB/s sequential read speed.", 5699, 4.6, 980, ["TechKart", "ByteBazaar"]),
    ("Logitech C920 HD Pro Webcam", "Full HD 1080p streaming and video conferencing webcam with dual stereo microphones.", 6495, 4.6, 1320, ["TechKart", "GadgetHub"]),
    ("TP-Link Archer AX55 WiFi 6 Router", "Dual-band AX3000 Gigabit WiFi 6 router with 4 high-gain antennas and HomeShield.", 5499, 4.5, 860, ["ByteBazaar", "MegaStore", "ValueMart"]),
    ("Epson EcoTank L3250 All-in-One Printer", "WiFi color ink tank printer, scanner, and copier with ultra-low cost per page.", 13999, 4.4, 1540, ["MegaStore", "TechKart"]),
    ("HP Smart Tank 580 Wireless Printer", "High-volume WiFi ink tank printer with spill-free refill bottles and mobile app print.", 14499, 4.3, 720, ["MegaStore", "ValueMart"]),

    # 6. Cameras & Gaming (8)
    ("Sony Alpha ZV-E10 Mirrorless Camera", "24.2MP APS-C vlogging mirrorless camera with 16-50mm power zoom kit lens and 4K video.", 61490, 4.7, 460, ["TechKart", "GadgetHub", "ShopSphere"]),
    ("Canon EOS R50 Mirrorless Camera", "Lightweight 24.2MP RF-mount mirrorless camera with Dual Pixel autofocus and 18-45mm lens.", 66990, 4.6, 310, ["TechKart", "MegaStore"]),
    ("GoPro HERO12 Black Action Camera", "Waterproof 5.3K60 HDR action camera with HyperSmooth 6.0 stabilization.", 37990, 4.6, 590, ["GadgetHub", "ShopSphere", "ByteBazaar"]),
    ("DJI Mini 3 Camera Drone", "Sub-249g foldable 4K HDR camera drone with true vertical shooting and 38-min flight.", 48990, 4.7, 290, ["GadgetHub", "ByteBazaar"]),
    ("Fujifilm Instax Mini 12 Instant Camera", "Fun instant film camera with automatic exposure and built-in selfie mirror.", 7499, 4.5, 1180, ["ShopSphere", "ValueMart", "GadgetHub"]),
    ("Sony PlayStation 5 Slim Console", "Next-gen 4K gaming console with 1TB ultra-high-speed SSD and DualSense controller.", 54990, 4.8, 1740, ["TechKart", "ByteBazaar", "MegaStore"]),
    ("Nintendo Switch OLED Gaming Console", "Hybrid handheld and TV gaming console with vibrant 7-inch OLED screen.", 31999, 4.7, 830, ["ByteBazaar", "GadgetHub"]),
    ("Microsoft Xbox Series S Console", "Compact all-digital 1440p gaming console with 512GB NVMe SSD and Game Pass support.", 34990, 4.6, 670, ["TechKart", "MegaStore"]),

    # 7. Power Banks, Chargers & Accessories (7)
    ("Anker PowerCore 20000mAh Power Bank", "High-capacity USB-C portable battery pack with PowerIQ fast charging technology.", 3499, 4.6, 1120, ["GadgetHub", "TechKart", "ShopSphere"]),
    ("Mi Power Bank 3i 20000mAh Fast Charge", "Triple-port 18W fast charging lithium polymer power bank with low-power mode.", 2149, 4.4, 4820, ["MegaStore", "ValueMart", "GadgetHub"]),
    ("Ambrane Stylo 10000mAh Power Bank", "Compact 20W PD fast charging pocket power bank with Type-C input and output.", 1099, 4.2, 2340, ["ValueMart", "ShopSphere"]),
    ("Anker Nano 65W GaN Fast Charger", "Compact 3-port Gallium Nitride wall charger for laptops, tablets, and phones.", 3299, 4.7, 740, ["TechKart", "GadgetHub"]),
    ("Belkin BoostCharge 30W USB-C Charger", "PPS certified compact USB-C wall adapter for fast safe smartphone charging.", 1699, 4.5, 510, ["ByteBazaar", "ShopSphere"]),
    ("Portronics Mport 4C USB-C Hub", "4-in-1 aluminum USB-C multiport adapter with HDMI 4K, USB 3.0, and 100W PD pass-through.", 1199, 4.3, 890, ["ByteBazaar", "ValueMart"]),
    ("Spigen Rugged Armor Laptop Sleeve", "Shock-absorbent protective 15-inch laptop sleeve with carabineer and accessory pouch.", 2499, 4.6, 420, ["TechKart", "ShopSphere"]),

    # 8. Kitchen & Home Appliances (12)
    ("Philips Digital Air Fryer 4.1L", "Rapid Air technology healthy kitchen air fryer with 7 touch presets and keep-warm mode.", 7999, 4.5, 2640, ["MegaStore", "ShopSphere", "ValueMart"]),
    ("Prestige Iris Plus Mixer Grinder", "750W heavy-duty kitchen mixer grinder with 3 stainless steel jars and juicer jar.", 3199, 4.3, 3920, ["MegaStore", "ValueMart", "ShopSphere"]),
    ("Bosch 7kg Front Load Washing Machine", "5-Star inverter automatic front load washer with anti-tangle and hygiene steam.", 29990, 4.6, 1150, ["MegaStore", "ShopSphere"]),
    ("LG 242L Frost Free Refrigerator", "3-Star Smart Inverter double door refrigerator with Door Cooling+ and convertible mode.", 25490, 4.5, 1340, ["MegaStore", "ValueMart"]),
    ("Voltas 1.5 Ton 3 Star Split AC", "Inverter split air conditioner with copper condenser, 4-in-1 adjustable mode, and dust filter.", 33990, 4.3, 1680, ["MegaStore", "ShopSphere", "ValueMart"]),
    ("Dyson V8 Absolute Cordless Vacuum Cleaner", "Powerful bagless stick vacuum cleaner with 40-minute runtime and HEPA filtration.", 34900, 4.7, 690, ["ShopSphere", "MegaStore"]),
    ("Philips GC1905 Steam Iron", "1440W non-stick soleplate steam iron with continuous steam output and quick heat-up.", 1699, 4.4, 5120, ["ValueMart", "ShopSphere"]),
    ("Kent Grand Plus RO Water Purifier", "8L wall-mounted RO+UV+UF+TDS mineral water purifier with zero water wastage tech.", 16999, 4.4, 2190, ["MegaStore", "ValueMart"]),
    ("Morphy Richards 25L Microwave Oven", "Convection microwave oven with 200 autocook menus, grilling, and stainless steel cavity.", 11499, 4.3, 840, ["MegaStore", "ShopSphere"]),
    ("Pigeon Amaze Plus Electric Kettle 1.5L", "1500W stainless steel cordless electric kettle with auto shut-off for boiling water and tea.", 649, 4.2, 6840, ["ValueMart", "ShopSphere", "MegaStore"]),
    ("Nescafe E Smart Coffee Maker", "App-enabled insulated travel mug coffee maker for hot and cold frothy coffee.", 5499, 4.3, 470, ["ShopSphere", "GadgetHub"]),
    ("Bajaj Majesty 2-Slice Pop-up Toaster", "750W bread toaster with variable browning control, mid-cycle cancel, and crumb tray.", 1399, 4.2, 1930, ["ValueMart", "MegaStore"]),

    # 9. Personal Care & Grooming (8)
    ("Philips OneBlade Hybrid Beard Trimmer", "Wet and dry facial trimmer and shaver with dual-sided blade and 3 stubble combs.", 1799, 4.5, 3410, ["GadgetHub", "ShopSphere", "ValueMart"]),
    ("Braun Series 3 Electric Shaver", "Waterproof 3-flexible-blade foil electric razor with rechargeable NiMH battery.", 4999, 4.4, 820, ["ShopSphere", "MegaStore"]),
    ("Dyson Supersonic Hair Dryer", "Fast-drying intelligent heat-control hair dryer with magnetic styling attachments.", 36900, 4.8, 540, ["ShopSphere", "GadgetHub"]),
    ("Philips Thermoprotect Hair Dryer", "1600W foldable hair dryer with ThermoProtect temperature setting and cool air shot.", 1495, 4.4, 2980, ["ValueMart", "ShopSphere"]),
    ("Oral-B Vitality Electric Toothbrush", "Rechargeable oscillating electric toothbrush with 2-minute quadrant timer.", 1699, 4.5, 2240, ["MegaStore", "ValueMart", "ShopSphere"]),
    ("Philips Sonicare 3100 Electric Toothbrush", "Sonic technology electric toothbrush with pressure sensor and 14-day battery.", 3299, 4.6, 610, ["GadgetHub", "ShopSphere"]),
    ("Mi Beard Trimmer 2C Waterproof", "USB-C fast charging beard trimmer with 40 length settings and 90-minute runtime.", 1199, 4.3, 3890, ["GadgetHub", "ValueMart"]),
    ("Omron HEM 7120 Digital Blood Pressure Monitor", "Automatic upper-arm BP monitor with IntelliSense technology and irregular heartbeat alert.", 1999, 4.6, 4120, ["MegaStore", "ValueMart", "ShopSphere"]),

    # 10. Footwear, Bags & Travel (10)
    ("Nike Air Zoom Pegasus 40 Running Shoes", "Responsive daily road running shoes with React foam cushioning and breathable mesh.", 9495, 4.6, 780, ["ShopSphere", "MegaStore", "ValueMart"]),
    ("Adidas Ultraboost Light Running Shoes", "High-energy-return Boost midsole running shoes with Primeknit upper and Continental sole.", 13999, 4.7, 640, ["ShopSphere", "MegaStore"]),
    ("Puma Velocity Nitro 2 Running Shoes", "Lightweight nitrogen-infused foam running shoes with PUMAGRIP all-surface traction.", 6999, 4.5, 510, ["ShopSphere", "ValueMart"]),
    ("Skechers Go Walk Max Walking Shoes", "Ultra-cushioned slip-on everyday walking shoes with Goga Max high-rebound insole.", 4299, 4.5, 1460, ["MegaStore", "ValueMart", "ShopSphere"]),
    ("Woodland Leather Outdoor Boots", "Rugged nubuck leather trekking and outdoor boots with durable lugged rubber outsole.", 3895, 4.3, 1890, ["MegaStore", "ValueMart"]),
    ("American Tourister Kamiliant Cabin Suitcase", "55cm hardside polycarbonate cabin trolley luggage with 4 spinner wheels and TSA lock.", 3299, 4.4, 1620, ["ShopSphere", "ValueMart", "MegaStore"]),
    ("Safari Pentagon Hardside Trolley Bag", "Scratch-resistant polypropylene 65cm check-in travel suitcase with smooth 360 wheels.", 2999, 4.3, 2780, ["ValueMart", "MegaStore"]),
    ("Wildcraft Wiki 35L Laptop Backpack", "Water-resistant daily college and travel backpack with padded 15-inch laptop compartment.", 1599, 4.4, 3450, ["ShopSphere", "ValueMart", "MegaStore"]),
    ("Skybags Brat Casual School Backpack", "Lightweight 22L stylish everyday backpack with front organizer pocket and rain cover.", 799, 4.2, 4620, ["ValueMart", "ShopSphere"]),
    ("Tommy Hilfiger Leather Bi-Fold Wallet", "Genuine leather slim men wallet with RFID protection and multiple card slots.", 1899, 4.5, 1140, ["ShopSphere", "MegaStore"]),

    # 11. Fitness, Sports & Home Office (10)
    ("Boldfit Anti-Skid Yoga Mat 6mm", "Sweat-resistant EVA foam exercise and yoga mat with carrying strap for home workouts.", 699, 4.3, 5210, ["ShopSphere", "ValueMart"]),
    ("Kore PVC 20kg Home Gym Dumbbell Set", "Adjustable 20kg home fitness weight set with dumbbell rods, curl rod, and gym gloves.", 1899, 4.1, 3140, ["MegaStore", "ValueMart", "ShopSphere"]),
    ("Yonex ZR 100 Light Badminton Racquet", "Lightweight aluminum frame badminton racket with isometric head for beginners.", 649, 4.3, 2890, ["ShopSphere", "ValueMart"]),
    ("Nivia Storm Football Size 5", "Hand-stitched rubberized outdoor soccer football with high air retention butyl bladder.", 449, 4.2, 4120, ["ValueMart", "MegaStore"]),
    ("Cosco Championship Tennis Ball Pack", "Pack of 3 high-bounce durable felt tennis balls suitable for all court surfaces.", 399, 4.4, 1760, ["ValueMart", "ShopSphere"]),
    ("Decathlon Domyos Skipping Rope", "Ergonomic grip speed jump rope with smooth ball bearings for cardio workouts.", 399, 4.5, 2430, ["ShopSphere", "ValueMart"]),
    ("Green Soul Monster Ergonomic Office Chair", "High-back ergonomic desk and gaming chair with lumbar pillow, 4D armrests, and recline.", 16990, 4.5, 1280, ["MegaStore", "ShopSphere", "TechKart"]),
    ("Wakefit Orthopedic Memory Foam Mattress", "Queen-size 6-inch medium-firm ergonomic memory foam mattress with breathable cover.", 11499, 4.5, 3640, ["MegaStore", "ShopSphere"]),
    ("Milton Thermosteel 1000ml Water Bottle", "Vacuum insulated stainless steel flask keeping beverages hot or cold for 24 hours.", 949, 4.6, 7850, ["ValueMart", "ShopSphere", "MegaStore"]),
    ("Cello Puro Steel Insulated Flask", "900ml leakproof double-walled stainless steel sports and office water bottle.", 799, 4.4, 3290, ["ValueMart", "ShopSphere"]),
]

VENDOR_PROFILES = {
    "TechKart":   {"price_mult": 1.00, "rating_delta": +0.1, "rev_mult": 1.05, "domain": "techkart.example.com"},
    "MegaStore":  {"price_mult": 1.04, "rating_delta": -0.1, "rev_mult": 0.90, "domain": "megastore.example.com"},
    "ByteBazaar": {"price_mult": 0.98, "rating_delta": +0.0, "rev_mult": 0.85, "domain": "bytebazaar.example.com"},
    "GadgetHub":  {"price_mult": 0.96, "rating_delta": +0.0, "rev_mult": 0.78, "domain": "gadgethub.example.com"},
    "ShopSphere": {"price_mult": 1.02, "rating_delta": +0.1, "rev_mult": 1.15, "domain": "shopsphere.example.com"},
    "ValueMart":  {"price_mult": 0.94, "rating_delta": -0.1, "rev_mult": 1.25, "domain": "valuemart.example.com"},
}

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

def build_catalog():
    os.makedirs("sample_sites", exist_ok=True)
    vendor_items = {v: list(items) for v, items in BASE_LISTINGS.items()}

    for idx, (title, desc, base_price, base_rating, base_reviews, vendors) in enumerate(GENERAL_PRODUCTS):
        slug = slugify(title)
        for v_idx, vendor in enumerate(vendors):
            prof = VENDOR_PROFILES[vendor]
            raw_price = base_price * prof["price_mult"]
            step = 50 if base_price >= 5000 else (10 if base_price >= 500 else 5)
            price = max(step, int(round(raw_price / step) * step))
            rating = round(min(4.9, max(3.6, base_rating + prof["rating_delta"])), 1)
            reviews = max(25, int(base_reviews * prof["rev_mult"]))
            availability = "Out of Stock" if (v_idx == len(vendors) - 1 and idx % 12 == 5) else "In Stock"
            url = f"https://{prof['domain']}/{slug}"
            vendor_items[vendor].append((title, desc, price, rating, reviews, availability, url))

    for vendor, items in vendor_items.items():
        articles = []
        for title, desc, price, rating, reviews, avail, url in items:
            articles.append(
                f'    <article class="product" data-price="{price}" data-rating="{rating}" '
                f'data-reviews="{reviews}" data-availability="{html.escape(avail)}">\n'
                f'      <h2 class="title">{html.escape(title)}</h2>\n'
                f'      <p class="desc">{html.escape(desc)}</p>\n'
                f'      <a class="product-url" href="{html.escape(url)}">View</a>\n'
                f'    </article>'
            )
        page_html = (
            f'<!DOCTYPE html>\n<html><head><title>{html.escape(vendor)}</title>'
            f'<script>console.log("ad");</script></head>\n<body>\n'
            f'  <nav>{html.escape(vendor)} Home | Categories | Cart</nav>\n'
            f'  <aside class="ad-banner">BUY NOW AD 99% OFF</aside>\n'
            f'  <div class="sidebar">Sponsored Ad Sidebar</div>\n'
            f'  <main>\n' + "\n".join(articles) + '\n  </main>\n'
            f'  <footer>Copyright {html.escape(vendor)}</footer>\n</body></html>\n'
        )
        with open(f"sample_sites/{vendor.lower()}.html", "w", encoding="utf-8") as f:
            f.write(page_html)

    ignore_kw = {"with", "and", "for", "the", "from", "inch", "all", "into", "that", "your"}
    sources_list = []
    for vendor, items in vendor_items.items():
        kw_set = set()
        for title, desc, *_ in items:
            for tok in re.findall(r"[a-z0-9]+", f"{title} {desc}".lower()):
                if len(tok) >= 2 and tok not in ignore_kw:
                    kw_set.add(tok)
        if vendor in {"GadgetHub", "ShopSphere", "ValueMart"}:
            kw_set.discard("mechanical")
            kw_set.discard("keyboard")
        sources_list.append({
            "name": vendor,
            "url": f"file://sample_sites/{vendor.lower()}.html",
            "keywords": sorted(kw_set),
        })

    sources_list.append({
        "name": "UnreachableVendor",
        "url": "http://127.0.0.1:1/unreachable",
        "keywords": ["keyboard", "mechanical", "laptop", "headphones", "smartphone", "shoes", "watch"]
    })

    with open("sources.json", "w", encoding="utf-8") as f:
        json.dump({"sources": sources_list}, f, indent=2)

    total_listings = sum(len(v) for v in vendor_items.values())
    print(f"Generated {len(vendor_items)} vendor HTML sites with {len(GENERAL_PRODUCTS) + 8} unique products ({total_listings} total listings) and updated sources.json.")

if __name__ == "__main__":
    build_catalog()
