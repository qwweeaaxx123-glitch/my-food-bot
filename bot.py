import random
import json
import os
import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

# 🎯 توكن البوت الخاص بك
TOKEN = "8072288284:AAHvqgYx-ma6S90T4oDvu9pzLAb1pisY7oM"

# 📂 ملف حفظ البيانات
DATA_FILE = "users.json"

# 🧠 تحميل البيانات
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 💾 حفظ البيانات
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_db, f, ensure_ascii=False, indent=2)

# 🕒 فحص التجديد اليومي
def check_daily_reset(uid):
    today = datetime.date.today().isoformat()
    if user_db[uid].get("last_reset") != today:
        user_db[uid]["att"] = 10
        user_db[uid]["last_reset"] = today
        save_data()

# 📸 بيانات الأكلات
FOOD_DATA = [
    {"img": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400", "ans": "برجر", "opt": ["برجر", "بيتزا", "شاورما", "سوشي"]},
    {"img": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400", "ans": "بيتزا", "opt": ["تاكو", "بيتزا", "نودلز", "ستيك"]},
    {"img": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400", "ans": "سلطة", "opt": ["سلطة", "شوربة", "كباب", "توفو"]}
]

user_db = load_data()

# 🔘 القوائم
def get_main_menu():
    return ReplyKeyboardMarkup([
        ['🍎 ابدأ اللعبة'],
        ['👤 الملف الشخصي', 'ℹ️ الأسئلة الشائعة'],
        ['💰 سحب الفلوس', '📜 سجل السحب'],
        ['💰 فلوس أكثر']
    ], resize_keyboard=True)

# 🚀 بدء التشغيل
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_db:
        user_db[uid] = {"bal": 0, "att": 10, "state": None, "bonus": False, "last_reset": datetime.date.today().isoformat()}
        save_data()
    else:
        check_daily_reset(uid)

    msg = "👋 أهلاً بكِ في FoodGuesser!\n\nخمن الأكلة واربح فلوس حقيقية! 💰\n📢 قناتنا: @Shaikh_PUBG"
    await update.message.reply_text(msg, reply_markup=get_main_menu())

# 🧩 إرسال سؤال
async def send_q(update, context, uid, feedback=""):
    food = random.choice(FOOD_DATA)
    opts = food["opt"].copy()
    random.shuffle(opts)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(opts[0], callback_data=f"v_{opts[0]}_{food['ans']}"),
         InlineKeyboardButton(opts[1], callback_data=f"v_{opts[1]}_{food['ans']}")],
        [InlineKeyboardButton(opts[2], callback_data=f"v_{opts[2]}_{food['ans']}"),
         InlineKeyboardButton(opts[3], callback_data=f"v_{opts[3]}_{food['ans']}")]
    ])
    cap = f"{feedback}\n\n🍟 خمن الأكلة!\n💰 المجموع: {user_db[uid]['bal']} IQD\n📊 الباقي: {user_db[uid]['att']}/10"
    if update.callback_query:
        await update.callback_query.message.delete()
    await context.bot.send_photo(chat_id=uid, photo=food["img"], caption=cap, reply_markup=kb)

# 💬 التعامل مع النصوص
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    txt = update.message.text
    if uid not in user_db:
        user_db[uid] = {"bal": 0, "att": 10, "state": None, "bonus": False, "last_reset": datetime.date.today().isoformat()}
        save_data()
    else:
        check_daily_reset(uid)

    # 🔄 نظام السحب
    if user_db[uid]["state"] == "S":
        if txt.isdigit():
            val = int(txt)
            if val < 250000:
                await update.message.reply_text(f"❗ الحد الأدنى للسحب هو 250,000 IQD.\nرصيدك: {user_db[uid]['bal']}\nاكتب المبلغ 👇")
            elif val > user_db[uid]["bal"]:
                await update.message.reply_text(f"⚠️ الفلوس ما تكفي\nرصيدك: {user_db[uid]['bal']}\nاكتب المبلغ 👇")
            else:
                await update.message.reply_text("✅ تم تقديم طلب السحب بنجاح!", reply_markup=get_main_menu())
                user_db[uid]["state"] = None
                save_data()
        return

    # 🧠 الأوامر
    if txt == '🍎 ابدأ اللعبة':
        if user_db[uid]["att"] > 0:
            await send_q(update, context, uid)
        else:
            await update.message.reply_text("❌ انتهت محاولاتك اليوم!")

    elif txt == '💰 فلوس أكثر':
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("اشترك ↗️", url="https://t.me/Shaikh_PUBG")],
            [InlineKeyboardButton("مشتركت ✅", callback_data="get_45")]
        ])
        await update.message.reply_text("❓ تريد تربح IQD 45000 زيادة؟\n\nاشترك بالقناة واضغط مشتركت ✅", reply_markup=kb)

    elif txt == '💰 سحب الفلوس':
        kb_s = ReplyKeyboardMarkup([['Zain Cash', 'Asia Hawala'], ['Fast Pay', 'Qi Card']], resize_keyboard=True)
        await update.message.reply_text("اختر وسيلة السحب:", reply_markup=kb_s)

    elif txt in ['Zain Cash', 'Asia Hawala', 'Fast Pay', 'Qi Card']:
        user_db[uid]["state"] = "S"
        save_data()
        await update.message.reply_text(f"اخترت {txt}\nاكتب المبلغ الذي تريد سحبه 👇", reply_markup=ReplyKeyboardRemove())

    elif txt == '👤 الملف الشخصي':
        await update.message.reply_text(f"👤 {update.effective_user.first_name}\n💰 الرصيد: {user_db[uid]['bal']} IQD\n📊 المحاولات: {user_db[uid]['att']}/10")

    elif txt == 'ℹ️ الأسئلة الشائعة':
        await update.message.reply_text("بوت تخمين الأكلات: خمن واربح جوائز نقدية. تابع @Shaikh_PUBG")

    elif txt == '📜 سجل السحب':
        await update.message.reply_text("📭 سجل السحب فارغ حالياً.")

# 🎯 التعامل مع الأزرار
async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if query.data == "get_45":
        if user_db[uid]["bonus"]:
            await query.message.reply_text("❌ استلمت الجائزة سابقاً!")
        else:
            user_db[uid]["bal"] += 45000
            user_db[uid]["bonus"] = True
            save_data()
            await query.message.reply_text(f"✅ تمت إضافة 45,000 IQD!\nرصيدك: {user_db[uid]['bal']}")
        return

    _, choice, correct = query.data.split("_")
    user_db[uid]["att"] -= 1
    res = "✅ صح! (+1800)" if choice == correct else f"❌ خطأ! (الصح: {correct})"
    if choice == correct:
        user_db[uid]["bal"] += 1800
    save_data()

    if user_db[uid]["att"] > 0:
        await send_q(update, context, uid, feedback=res)
    else:
        await query.message.delete()
        await context.bot.send_message(uid, f"{res}\n🏁 انتهت المحاولات!", reply_markup=get_main_menu())

# 🏁 تشغيل البوت
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_call))
    print("✅ البوت يعمل الآن...")
    app.run_polling()
