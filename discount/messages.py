def discount_wa_message(booking, discount):
    if discount.discount_type == 'percent':
        diskon = f"{discount.discount_value}%"
    else:
        diskon = f"Rp {discount.discount_value:,}".replace(",", ".")

    return f"""
🎉 *DISKON SPESIAL UNTUK ANDA!*

Halo *{booking.name}* 👋  
Noble Studio memberikan diskon khusus:

💰 Diskon: *{diskon}*  
📅 Berlaku sampai: *{discount.expired_at.strftime('%d %B %Y %H:%M')}*

✨ Gunakan sekarang sebelum berakhir!

🔗 Booking:
https://noblestudio.com/booking

Terima kasih 🙏
*Noble Studio*
"""
