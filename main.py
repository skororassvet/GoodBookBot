import telebot
from telebot import types
import config as keys
import ParserGr as GoodReads
import ParserWs as WaterStones
import ParserAbe as AbeBooks
import TitlesISBN as TitleToISBN
from sqlite import SQLite


bot = telebot.TeleBot(keys.TOKEN)
print("Telebot initiated")
db = SQLite('db.db')
print("Db initiated")
print("Bot is live.")


@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.send_message(message.chat.id,
                     text='''
                     Welcome to GoodBookBot!
To start searching simply type a book's title.
To achieve best accuracy type in this template: 
<book title> <author> eg. The Outsider Camus
There is also a /help command!
Have fun! (:''')


@bot.message_handler(commands=['help'])
def start(message):
    bot.send_message(message.chat.id,
                     text='''
        Available commands:
/help - get the command list
/start - launch a bot
/tbr - see your tbr list
/read - see your read list'''
                     )


@bot.message_handler(commands=['tbr'])
def tbr_list(message):
    user_id = message.from_user.id

    # If there are books marked tbr
    if db.tbr_exists(user_id):
        tbr = ""
        for row in db.select_tbr(user_id):
            entry = str(row).replace("(", "").replace(",)", "")
            title = AbeBooks.ParserAbe(entry).title
            tbr += ("\nඩ " + title)
        bot.send_message(message.chat.id, 'Here is your TBR list: ')
        bot.send_message(message.chat.id, tbr)
    else:
        bot.send_message(message.chat.id, 'Your TBR list is empty! Add some books first!')


@bot.message_handler(commands=['read'])
def read_list(message):
    user_id = message.from_user.id

    # If there are books marked as read
    if db.read_exists(user_id):
        read = ""
        # Prints the list
        for row in db.select_read(user_id):
            entry = str(row).replace("('", "").replace("',)", "")
            title = AbeBooks.ParserAbe(entry).title
            read += ("\nඩ " + title)
        bot.send_message(message.chat.id, 'Here is your *Read* list: ')
        bot.send_message(message.chat.id, read)
    else:
        bot.send_message(message.chat.id, 'Your *Read* list is empty! Add some books first!')


@bot.message_handler(content_types=['text'])
def search(message):
    isbn = TitleToISBN.TitlesISBN(message.text).isbn
    user_id = message.from_user.id

    # Adds buttons to a message
    markup = types.InlineKeyboardMarkup(row_width=2)
    item1 = types.InlineKeyboardButton("TBR", callback_data=f'tbr{isbn}')
    item2 = types.InlineKeyboardButton("Read", callback_data=f'red{isbn}')
    item3 = types.InlineKeyboardButton("Delete", callback_data=f'dlt{isbn}')
    item4 = types.InlineKeyboardButton("Rate", callback_data=f'rat{isbn}')
    markup.add(item1, item2, item3, item4)

    # Adds hyperlinks
    hyperlinkabe = f"<a href='{AbeBooks.ParserAbe(isbn).link}'>{AbeBooks.ParserAbe(isbn).price_used}</a>"
    hyperlinkws = f"<a href='{WaterStones.ParserWs(isbn).link}'>{WaterStones.ParserWs(isbn).price_new}</a>"
    s = ""
    r = ""

    for row in check_status(user_id, isbn):
        s = row
    status = str(s).replace("('", "").replace("',)", "")

    for row in check_rating(user_id, isbn):
        r = row
    rating = str(r).replace("(", "").replace(",)", "")

    bot.send_message(message.chat.id,
                     text=f'''
    Title: {AbeBooks.ParserAbe(isbn).title}
    Author: {AbeBooks.ParserAbe(isbn).author}
    Price, used: {hyperlinkabe}
    Price, new: {hyperlinkws}
    GoodReads rating: {GoodReads.ParserGr(isbn).rating_gr}
    Your rating: {rating}
    Your status: {status}
            ''', reply_markup=markup, parse_mode='html')


@bot.callback_query_handler(func=lambda call: True)
# Handles buttons under book's description
def callback_inline(call):
    try:
        if call.message:
            if call.data.startswith("tbr"):
                isbn = call.data.replace("tbr", "")
                if not db.entry_exists(call.from_user.id, isbn):
                    # creates an entry for this user and updates this book's status to tbr
                    db.create_entry_tbr(call.from_user.id, isbn)
                    bot.send_message(call.message.chat.id, "The book was successfully added to your TBR list.")
                else:
                    # updates this book's status to tbr
                    db.update_status_tbr(call.from_user.id, isbn)
                    bot.send_message(call.message.chat.id, "The book was successfully added to your TBR list.")

            elif call.data.startswith("red"):
                isbn = call.data.replace("red", "")
                if not db.entry_exists(call.from_user.id, isbn):
                    # creates an entry for this user and updates this book's status to read
                    db.create_entry_read(call.from_user.id, isbn)
                    bot.send_message(call.message.chat.id, "The book was successfully added to your *Read* list.")
                else:
                    # updates this book's status to read
                    db.update_status_read(call.from_user.id, isbn)
                    bot.send_message(call.message.chat.id, "The book was successfully added to your *Read* list.")

            elif call.data.startswith("dlt"):
                isbn = call.data.replace("dlt", "")
                if db.entry_exists(call.from_user.id, isbn):
                    # deletes a book from a db
                    db.delete_entry(call.from_user.id, isbn)
                    bot.send_message(call.message.chat.id, "The book was successfully deleted from your list.")
                else:
                    bot.send_message(call.message.chat.id, "The books isn't on your list.")

            elif call.data.startswith("rat"):
                isbn = call.data.replace("rat", "")
                bot.send_message(call.message.chat.id, "How was your read?", reply_markup=ratings(isbn))

            elif call.data.startswith("1s"):
                isbn = call.data.replace("1s", "")
                if not db.entry_exists(call.from_user.id, isbn):
                    # creates an entry and gives a rating to it
                    db.create_entry_rating(call.from_user.id, isbn, 1)
                    bot.send_message(call.message.chat.id, "The book has been rated 1 star.")
                else:
                    # updates a rating for this book
                    db.update_status_rating(call.from_user.id, isbn, 1)
                    bot.send_message(call.message.chat.id, "The book has been rated 1 star.")

            elif call.data.startswith("2s"):
                isbn = call.data.replace("2s", "")
                if not db.entry_exists(call.from_user.id, isbn):
                    # creates an entry and gives a rating to it
                    db.create_entry_rating(call.from_user.id, isbn, 2)
                    bot.send_message(call.message.chat.id, "The book has been rated 2 stars.")
                else:
                    # updates a rating for this book
                    db.update_status_rating(call.from_user.id, isbn, 2)
                    bot.send_message(call.message.chat.id, "The book has been rated 2 stars.")

            elif call.data.startswith("3s"):
                isbn = call.data.replace("3s", "")
                if not db.entry_exists(call.message.from_user.id, isbn):
                    # creates an entry and gives a rating to it
                    db.create_entry_rating(call.from_user.id, isbn, 3)
                    bot.send_message(call.message.chat.id, "The book has been rated 3 stars.")
                else:
                    # updates a rating for this book
                    db.update_status_rating(call.from_user.id, isbn, 3)
                    bot.send_message(call.message.chat.id, "The book has been rated 3 stars.")

            elif call.data.startswith("4s"):
                isbn = call.data.replace("4s", "")
                if not db.entry_exists(call.message.from_user.id, isbn):
                    # creates an entry and gives a rating to it
                    db.create_entry_rating(call.from_user.id, isbn, 4)
                    bot.send_message(call.message.chat.id, "The book has been rated 4 stars.")
                else:
                    # updates a rating for this book
                    db.update_status_rating(call.from_user.id, isbn, 4)
                    bot.send_message(call.message.chat.id, "The book has been rated 4 stars.")

            elif call.data.startswith("5s"):
                isbn = call.data.replace("5s", "")
                if not db.entry_exists(call.from_user.id, isbn):
                    # creates an entry and gives a rating to it
                    db.create_entry_rating(call.from_user.id, isbn, 5)
                    bot.send_message(call.message.chat.id, "The book has been rated 5 stars.")
                else:
                    # updates a rating for this book
                    db.update_status_rating(call.from_user.id, isbn, 5)
                    bot.send_message(call.message.chat.id, "The book has been rated 5 stars.")

    except Exception as e:
        print(f"Button didn't work: {e}")


def ratings(isbn):
    # Creates five buttons for the user to rate a book
    markup = types.InlineKeyboardMarkup(row_width=2)
    rating1 = types.InlineKeyboardButton("1", callback_data=f"1s{isbn}")
    rating2 = types.InlineKeyboardButton("2", callback_data=f"2s{isbn}")
    rating3 = types.InlineKeyboardButton("3", callback_data=f"3s{isbn}")
    rating4 = types.InlineKeyboardButton("4", callback_data=f"4s{isbn}")
    rating5 = types.InlineKeyboardButton("5", callback_data=f"5s{isbn}")
    markup.add(rating1, rating2, rating3, rating4, rating5)
    return markup


def check_rating(user_id, isbn):
    if not (db.rating_exists(user_id, isbn)):
        return "-"
    else:
        return db.select_rating(user_id, isbn)


def check_status(user_id, isbn):
    if not (db.status_exists(user_id, isbn)):
        return "-"
    else:
        return db.select_status(user_id, isbn)


# starts polling
if __name__ == '__main__':
    bot.polling()
