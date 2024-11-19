import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import time
from threading import Thread
import database  # استيراد وحدة قاعدة البيانات
from config import *
# تهيئة قاعدة البيانات
database.create_table()


bot = telebot.TeleBot(TOKEN)



# رسالة الترحيب
@bot.message_handler(commands=['start'])
def start_command(message):
    if message.from_user.id == ADMIN_ID:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("👑 إدارة البوت"))
        bot.send_message(message.chat.id, "مرحبًا عزيزي المطور! هذه لوحة التحكم الخاصة بك.", reply_markup=markup)
    else:
        bot.send_message(
            message.chat.id,
            "مرحبًا بك في بوت الإعلانات! سيتم نشر إعلانك في القناة. "
            "إذا حصل إعلانك على 100 👍 خلال 3 ساعات، سيتم تثبيته. "
            "أرسل إعلانك الآن ⬇️"
        )

# لوحة تحكم المطور
@bot.message_handler(func=lambda message: message.text == "👑 إدارة البوت")
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("✋ إغلاق استقبال النصوص", "✅ فتح استقبال النصوص")
        markup.add("✋ إغلاق استقبال الوسائط", "✅ فتح استقبال الوسائط")
        markup.add("✋ إغلاق استقبال الملصقات", "✅ فتح استقبال الملصقات")
        markup.add("🚫 حظر مستخدم", "🔓 إزالة حظر")
        bot.send_message(message.chat.id, "🔧 إعدادات البوت:", reply_markup=markup)


# Echo photos with captions
@bot.message_handler(content_types=['photo'])
def echo_photo(message):
    user_id = message.from_user.id
        # تحقق من حد الرسائل للمستخدم
    if not database.update_user_message_limit(user_id):
        bot.reply_to(message, "🚫 عذرًا، لقد وصلت إلى حدك المسموح به من 2 رسالة خلال الـ 24 ساعة الماضية.")
        return
    likes_count[message.message_id] = 0
    # Create the like button
    markup = InlineKeyboardMarkup()
    like_button = InlineKeyboardButton(f"👍 {likes_count[message.message_id]}", callback_data=f"like:{user_id}")
    markup.add(like_button)

    file_id = message.photo[-1].file_id  # Get the highest resolution photo
    caption = message.caption if message.caption else ""
    msg = bot.send_photo(CHANNEL_ID, file_id, caption=caption, reply_markup=markup)

    database.insert_message(msg.message_id, user_id)

    # Notify the admin about the new message
    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(InlineKeyboardButton("🗑️ إزالة", callback_data=f"remove:{msg.message_id}:{user_id}"))
    admin_markup.add(InlineKeyboardButton("✅ احتفظ", callback_data=f"keep:{msg.message_id}"))
    
    # Construct the account link
    account_link = f"https://t.me/{user_id}"  # This will link to the user's profile
    the_text = caption if message.caption else "لا يوجد نص!"

    admin_message = bot.send_message(
        ADMIN_ID,
        f"📩 رسالة جديدة من المستخدم {user_id}:\nرابط الحساب: {account_link}\nنص الرسالة: {the_text}\nرابط الرسالة: https://t.me/{CHANNEL_ID[1:]}/{msg.message_id}",
        reply_markup=admin_markup
    )

    # Start monitoring likes
    Thread(target=monitor_message, args=(msg.message_id,)).start()
    bot.reply_to(message, "✅ تم نشر إعلانك بنجاح!")


@bot.message_handler(content_types=['video'])
def echo_video(message):
    user_id = message.from_user.id
        # تحقق من حد الرسائل للمستخدم
    if not database.update_user_message_limit(user_id):
        bot.reply_to(message, "🚫 عذرًا، لقد وصلت إلى حدك المسموح به من 2 رسالة خلال الـ 24 ساعة الماضية.")
        return
    likes_count[message.message_id] = 0
    
    file_id = message.video.file_id
    # Create the like button
    markup = InlineKeyboardMarkup()
    like_button = InlineKeyboardButton(f"👍 {likes_count[message.message_id]}", callback_data=f"like:{user_id}")
    markup.add(like_button)
    caption = message.caption if message.caption else ""
    msg = bot.send_video(CHANNEL_ID, file_id, caption=caption, reply_markup=markup)

    database.insert_message(msg.message_id, user_id)

    # Notify the admin about the new message
    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(InlineKeyboardButton("🗑️ إزالة", callback_data=f"remove:{msg.message_id}:{user_id}"))
    admin_markup.add(InlineKeyboardButton("✅ احتفظ", callback_data=f"keep:{msg.message_id}"))
    
    # Construct the account link
    account_link = f"https://t.me/{user_id}"  # This will link to the user's profile
    the_text = caption if message.caption else "لا يوجد نص!"
    admin_message = bot.send_message(
        ADMIN_ID,
        f"📩 رسالة جديدة من المستخدم {user_id}:\nرابط الحساب: {account_link}\nنص الرسالة: {the_text}\nرابط الرسالة: https://t.me/{CHANNEL_ID[1:]}/{msg.message_id}",
        reply_markup=admin_markup
    )




# إرسال الإعلانات للقناة
@bot.message_handler(func=lambda message: True)  # Handle all messages
def handle_advertisement(message):
    user_id = message.from_user.id
    if message.from_user.id == ADMIN_ID:
        return

    print(f"new message: \n {message}")

    # تحقق من حد الرسائل للمستخدم
    if not database.update_user_message_limit(user_id):
        bot.reply_to(message, "🚫 عذرًا، لقد وصلت إلى حدك المسموح به من 2 رسالة خلال الـ 24 ساعة الماضية.")
        return

    # منع المستخدمين المحظورين
    if user_id in settings["banned_users"]:
        bot.reply_to(message, "🚫 عذرًا، لقد تم حظرك من استخدام البوت.")
        return

    # التحقق من الإعدادات
    if not settings["accept_text"] and message.text:
        bot.reply_to(message, "🚫 استقبال الرسائل النصية مغلق حاليًا.")
        return
    if not settings["accept_media"] and message.content_type in ['photo', 'video']:
        bot.reply_to(message, "🚫 استقبال الوسائط مغلق حاليًا.")
        return
    if not settings["accept_stickers"] and message.sticker:
        bot.reply_to(message, "🚫 استقبال الملصقات مغلق حاليًا.")
        return

    # نشر الرسالة في القناة
    try:
        # Initialize likes count
        likes_count[message.message_id] = 0
        
        # Create the like button
        markup = InlineKeyboardMarkup()
        like_button = InlineKeyboardButton(f"👍 {likes_count[message.message_id]}", callback_data=f"like:{user_id}")
        markup.add(like_button)

        # Check the type of message and send accordingly
        if message.content_type == 'text':
            print(f"Received text message: {message.text}")  # Debugging print
            # Send only text
            msg = bot.send_message(
                CHANNEL_ID,
                message.text,
                reply_markup=markup  # تضمين زر الإعجاب في الرسالة
            )

        else:
            print(f"Received unsupported message type: {message.content_type}")  # Debugging print
            bot.reply_to(message, "🚫 نوع الرسالة غير مدعوم.")

        # Insert the message into the database
        database.insert_message(msg.message_id, user_id)

        # Notify the admin about the new message
        admin_markup = InlineKeyboardMarkup()
        admin_markup.add(InlineKeyboardButton("🗑️ إزالة", callback_data=f"remove:{msg.message_id}:{user_id}"))
        admin_markup.add(InlineKeyboardButton("✅ احتفظ", callback_data=f"keep:{msg.message_id}"))
        
        # Construct the account link
        account_link = f"https://t.me/{user_id}"  # This will link to the user's profile

        admin_message = bot.send_message(
            ADMIN_ID,
            f"📩 رسالة جديدة من المستخدم {user_id}:\nرابط الحساب: {account_link}\nنص الرسالة: {message.text}\nرابط الرسالة: https://t.me/{CHANNEL_ID[1:]}/{msg.message_id}",
            reply_markup=admin_markup
        )

        # Start monitoring likes
        Thread(target=monitor_message, args=(msg.message_id,)).start()
        bot.reply_to(message, "✅ تم نشر إعلانك بنجاح!")
    except Exception as e:
        bot.reply_to(message, "❌ حدث خطأ أثناء النشر. يرجى التحقق من إعدادات القناة.")
        print(f"Error: {e}")

# التحقق من التفاعل
def monitor_message(message_id):
    time.sleep(10800)  # 3 ساعات
    try:
        if likes_count.get(message_id, 0) >= 100:
            bot.pin_chat_message(CHANNEL_ID, message_id)
        else:
            bot.delete_message(CHANNEL_ID, message_id)
    except Exception as e:
        print(f"خطأ في مراقبة الرسالة: {e}")

# معالجة اللايكات
@bot.callback_query_handler(func=lambda call: call.data.startswith("like:"))
def handle_like(call):
    try:
        message_id = call.message.message_id
        user_id = call.from_user.id

        # Check if the user has already liked this message
        if user_id in user_likes.get(message_id, set()):
            bot.answer_callback_query(call.id, "❌ لقد قمت بالفعل بإعجاب هذه الرسالة!")
            return

        # Update the likes count and track the user
        likes_count[message_id] = database.get_likes(message_id) + 1  # Get current likes from the database
        user_likes.setdefault(message_id, set()).add(user_id)  # Add user to the set of users who liked this message

        # Update the database with the new likes count
        database.update_likes(message_id, likes_count[message_id])

        # تحديث زر اللايك
        markup = InlineKeyboardMarkup()
        like_button = InlineKeyboardButton(f"👍 {likes_count[message_id]}", callback_data=f"like:{user_id}")
        markup.add(like_button)
        bot.edit_message_reply_markup(CHANNEL_ID, message_id, reply_markup=markup)

        # إشعار المستخدم
        bot.answer_callback_query(call.id, "👍 تم احتساب إعجابك!")
    except Exception as e:
        print(f"خطأ في معالجة اللايك: {e}")

# معالجة إزالة الرسالة
@bot.callback_query_handler(func=lambda call: call.data.startswith("remove:"))
def handle_remove(call):
    try:
        _, message_id, user_id = call.data.split(":")
        message_id = int(message_id)
        
        # Remove the message from the channel
        bot.delete_message(CHANNEL_ID, message_id)
        
        # Notify the sender
        bot.send_message(user_id, "🚫 تم إزالة إعلانك من القناة بواسطة الإدارة.")
        
        # Clean the message data from the database
        database.delete_message(message_id)  # Delete the message from the database

        # Notify the admin that the action is done
        bot.edit_message_text("✅ تم التنفيذ ...", chat_id=ADMIN_ID, message_id=call.message.message_id)
        time.sleep(3)  # Wait for 3 seconds
        bot.delete_message(ADMIN_ID, call.message.message_id)  # Remove the original message from admin's chat

        bot.answer_callback_query(call.id, "✅ تم إزالة الرسالة.")
    except Exception as e:
        print(f"خطأ في إزالة الرسالة: {e}")

# معالجة الاحتفاظ بالرسالة
@bot.callback_query_handler(func=lambda call: call.data.startswith("keep:"))
def handle_keep(call):
    try:
        _, message_id = call.data.split(":")
        message_id = int(message_id)

        # Remove the like button from the message
        markup = InlineKeyboardMarkup()  # Create an empty markup to remove the button
        bot.edit_message_reply_markup(CHANNEL_ID, message_id, reply_markup=markup)

        # Notify the admin that the action is done
        bot.edit_message_text("✅ تم التنفيذ ...", chat_id=ADMIN_ID, message_id=call.message.message_id)
        time.sleep(3)  # Wait for 3 seconds
        bot.delete_message(ADMIN_ID, call.message.message_id)  # Remove the original message from admin's chat

        bot.answer_callback_query(call.id, "✅ تم الاحتفاظ بالرسالة.")
    except Exception as e:
        print(f"خطأ في الاحتفاظ بالرسلة: {e}")

# تشغيل
print("✅ البوت يعمل الآن...")
bot.polling()
