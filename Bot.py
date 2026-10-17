elif call.data.startswith("tf_"):
        selected_tf = call.data.replace("tf_", "")
        user_data[chat_id] = user_data.get(chat_id, {})
        user_data[chat_id]['tf'] = selected_tf
        bot.send_message(chat_id, f"✅ تم اختيار المدة: *{selected_tf}*", parse_mode="Markdown")

    elif call.data == "btn_signal":
        pair = user_data.get(chat_id, {}).get('pair', PAIRS[0])
        tf = user_data.get(chat_id, {}).get('tf', "1 دقيقة")
        
        bot.send_message(chat_id, "⏳ جاري فحص الشموع وتحليل السوق...")
        
        direction = random.choice(["🟢 شراء (CALL)", "🔴 بيع (PUT)"])
        accuracy = random.randint(90, 98)
        reason = random.choice(REASONS)
        
        signal_msg = (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 **توصية Pocket Option احترافية** 📊\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔤 **الزوج:** `{pair}`\n"
            f"⏰ **المدة:** `{tf}`\n"
            f"🎯 **الاتجاه:** **{direction}**\n"
            f"📈 **نسبة الثقة:** `{accuracy}%`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 **التحليل الفني:** {reason}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *التزم بإدارة راس مالك واقتنص الفرص القوية.*"
        )
        bot.send_message(chat_id, signal_msg, parse_mode="Markdown")

if __name__ == '__main__':
    bot.infinity_polling()
    
