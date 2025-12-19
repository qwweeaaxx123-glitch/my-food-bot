import sqlite3
import random
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest

# --- الإعدادات الأساسية ---
TOKEN = "8072288284:AAHvqgYx-ma6S90T4oDvu9pzLAb1pisY7oM"
CHANNEL_ID = "@Shaikh_PUBG"

# --- نظام قاعدة البيانات ---
class Database:
    def __init__(self, db_name="food_data.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                attempts INTEGER DEFAULT 10,
                bonus_claimed INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = self.cursor.fetchone()
        if not user:
            self.cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            self.conn.commit()
            return (user_id, 0, 10, 0)
        return user

    def update_balance(self, user_id, amount):
        self.cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        self.conn.commit()

    def use_attempt(self, user_id):
        self.cursor.execute("UPDATE users SET attempts = attempts - 1 WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def reset_attempts(self):
        self.cursor.execute("UPDATE users SET attempts = 10")
        self.conn.commit()

    def set_bonus(self, user_id):
        self.cursor.execute("UPDATE users SET bonus_claimed = 1 WHERE user_id = ?", (user_id,))
        self.conn.commit()

db = Database()
user_states = {}

# --- البيانات ---
FOOD_DATA = [
    {"img": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400", "ans": "برجر", "opt": ["برجر", "بيتزا", "شاورما", "سوشي"]},
    {"img": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400", "ans": "بيتزا", "opt": ["تاكو", "بيتزا", "نودلز", "ستيك"]},
    {"img": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400", "ans": "سلطة", "opt": ["سلطة", "شوربة", "كباب", "توفو"]}
]

# --- الكيبوردات ---
def get_main_menu():
    return ReplyKeyboardMarkup([
        ['🍎 ابدأ اللعبة'],
        ['👤 الملف الشخصي', 'ℹ️ الأسئلة الشائعة'],
        ['💰 سحب الفلوس', '📜 سجل السحب'],
        ['💰 فلوس أكثر']
    ], resize_keyboard=True)

def get_back_button():
    return ReplyKeyboardMarkup([['🔙 العودة للقائمة الرئيسية']], resize_keyboard=True)

# --- الوظائف ---
async def daily_reset_job(context: ContextTypes.DEFAULT_TYPE):
    db.reset_attempts()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    db.get_user(uid)
    await update.message.reply_text(
        "👋 أهلاً بك في بوت تخمين الأكلة!\nاربح IQD وجوائز حقيقية يومياً.",
        reply_markup=get_main_menu()
    )

async def send_q(update, context, uid, feedback=""):
    user = db.get_user(uid)
    food = random.choice(FOOD_DATA)
    opts = food["opt"].copy()
    random.shuffle(opts)
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(opts[0], callback_data=f"v_{opts[0]}_{food['ans']}"), InlineKeyboardButton(opts[1], callback_data=f"v_{opts[1]}_{food['ans']}")],
        [InlineKeyboardButton(opts[2], callback_data=f"v_{opts[2]}_{food['ans']}"), InlineKeyboardButton(opts[3], callback_data=f"v_{opts[3]}_{food['ans']}")]
    ])
    
    cap = f"{feedback}\n\n🍟 خمن الأكلة!\n💰 رصيدك: {user[1]:,} IQD\n📊 المحاولات: {user[2]}/10"
    
    if update.callback_query:
        try: await update.callback_query.message.delete()
        except: pass
        
    await context.bot.send_photo(chat_id=uid, photo=food["img"], caption=cap, reply_markup=kb)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    txt = update.message.text
    user = db.get_user(uid)

    if txt == '🔙 العودة للقائمة الرئيسية':
        user_states[uid] = None
        await update.message.reply_text("🔙 تم العودة للقائمة الرئيسية", reply_markup=get_main_menu())
        return

    if uid in user_states and user_states[uid] == "WITHDRAW_AMOUNT":
        if txt.isdigit():
            val = int(txt)
            if val < 250000:
                await update.message.reply_text(f"❗ الحد الأدنى للسحب هو 250,000 IQD.\nرصيدك الحالي: {user[1]:,}", reply_markup=get_back_button())
            elif val > user[1]:
                await update.message.reply_text(f"⚠️ رصيدك لا يكفي لسحب هذا المبلغ.\nرصيدك: {user[1]:,}", reply_markup=get_back_button())
            else:
                db.update_balance(uid, -val)
                await update.message.reply_text(f"✅ تم تقديم طلب سحب مبلغ {val:,} IQD بنجاح!", reply_markup=get_main_menu())
                user_states[uid] = None
        else:
            await update.message.reply_text("⚠️ يرجى إدخال أرقام فقط!")
        return

    if txt == '🍎 ابدأ اللعبة':
        if user[2] > 0: await send_q(update, context, uid)
        else: await update.message.reply_text("❌ انتهت محاولاتك اليوم! انتظر 24 ساعة للتجديد.")

    elif txt == '👤 الملف الشخصي':
        await update.message.reply_text(f"👤 الاسم: {update.effective_user.first_name}\n💰 الرصيد: {user[1]:,} IQD\n📊 المحاولات المتبقية: {user[2]}")

    elif txt == '💰 سحب الفلوس':
        kb = ReplyKeyboardMarkup([['Zain Cash', 'Asia Hawala'], ['Fast Pay', 'Qi Card'], ['🔙 العودة للقائمة الرئيسية']], resize_keyboard=True)
        await update.message.reply_text("اختر وسيلة السحب المفضلة:", reply_markup=kb)

    elif txt in ['Zain Cash', 'Asia Hawala', 'Fast Pay', 'Qi Card']:
        user_states[uid] = "WITHDRAW_AMOUNT"
        await update.message.reply_text(f"لقد اخترت {txt}.\nالآن اكتب المبلغ الذي تريد سحبه 👇", reply_markup=get_back_button())

    elif txt == '💰 فلوس أكثر':
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("اشترك في القناة ✅", callback_data="check_sub")]])
        await update.message.reply_text(f"اشترك في قناة {CHANNEL_ID} واحصل على 45,000 IQD مكافأة!", reply_markup=kb)

    elif txt == 'ℹ️ الأسئلة الشائعة':
        await update.message.reply_text("بوت تخمين الأكلات: خمن واربح مبالغ حقيقية.\nالحد الأدنى للسحب: 250,000 IQD")

    elif txt == '📜 سجل السحب':
        await update.message.reply_text("📭 سجل السحب الخاص بك فارغ حالياً.")

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    user = db.get_user(uid)
    await query.answer()

    if query.data == "check_sub":
        if user[3] == 1:
            await query.edit_message_text("❌ لقد استلمت المكافأة مسبقاً!")
            return
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=uid)
            if member.status in ['member', 'administrator', 'creator']:
                db.update_balance(uid, 45000)
                db.set_bonus(uid)
                await query.edit_message_text("✅ شكراً لاشتراكك! تمت إضافة 45,000 IQD لرصيدك.")
            else:
                await query.answer("⚠️ يجب عليك الاشتراك في القناة أولاً!", show_alert=True)
        except:
            await query.edit_message_text("❌ حدث خطأ. تأكد أن البوت مسؤول في القناة.")

    elif query.data.startswith("v_"):
        _, choice, correct = query.data.split("_")
        db.use_attempt(uid)
        
        if choice == correct:
            db.update_balance(uid, 1800)
            res = "✅ إجابة صحيحة! (+1800 IQD)"
        else:
            res = f"❌ إجابة خاطئة! الأكلة هي: {correct}"
            
        user_upd = db.get_user(uid)
        if user_upd[2] > 0:
            await send_q(update, context, uid, feedback=res)
        else:
            try: await query.message.delete()
            except: pass
            await context.bot.send_message(uid, f"{res}\n🏁 انتهت محاولاتك اليوم. عد غداً!", reply_markup=get_main_menu())

if __name__ == '__main__':
    # حل مشكلة الـ JobQueue في Pydroid
    app = Application.builder().token(TOKEN).build()
    
    # محاولة تشغيل التوقيت إذا كانت المكتبة تدعم ذلك
    if app.job_queue:
        app.job_queue.run_repeating(daily_reset_job, interval=86400, first=10)
        print("✅ نظام التوقيت اليومي يعمل.")
    else:
        print("⚠️ نظام التوقيت يعمل بشكل محدود بسبب بيئة التشغيل.")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_call))
    
    print("🚀 البوت بدأ العمل الآن...")
    app.run_polling(drop_pending_updates=True)
