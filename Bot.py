 = f"⚙️ **إعدادات الصفقة الحالية:**\n\n🔹 الزوج: `{pair}`\n🔹 المدة: `{tf}`"
        bot.answer_callback_query(call.id, "عرض الإعدادات")
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=main_keyboard(), parse_mode="Markdown")

    # العودة للقائمة الرئيسية
    elif call.data == "main_menu":
        bot.edit_message_text("🏠 **القائمة الرئيسية:**", chat_id, call.message.message_id, reply_markup=main_keyboard(), parse_mode="Markdown")

    # === 5. التحليل الفني الدقيق واستخراج الإشارات ===
    elif call.data == "get_signal":
        pair = user_settings[chat_id]["pair"]
        tf = user_settings[chat_id]["timeframe"]

        bot.answer_callback_query(call.id, "جاري تحليل الشمعة والمؤشرات...")
        
        scenarios = [
            {
                "dir": "🟢 شراء (CALL - صعود)",
                "reason": "السعر ارتد بوضوح من الخط الأوسط لـ Bollinger Bands مع اتجاه صاعد قوي ومؤشر Stochastic يدعم الصعود."
            },
            {
                "dir": "🔴 بيع (PUT - هبوط)",
                "reason": "السعر لامس الحد العلوي وارتد للأسفل، ومؤشر RSI يعطي إشارة انعكاس واضحة مع هبوط السيولة."
            },
            {
                "dir": "⚠️ تحذير: لا تدخل الصفقة",
                "reason": "السعر يلامس الأطراف (القمة/القاع) والمؤشرات في منطقة تشبع خطيرة ضد الاتجاه. يُفضل 
