import logging
import nest_asyncio
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Patch asyncio to allow nested loops
nest_asyncio.apply()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Set your admin user ID
ADMIN_USER_ID = 70575486  # Replace with your actual Telegram user ID

# Define questions for the therapy bot
questions = [
    "سلام! نام شما چیست؟",
    "چند سال دارید؟",
    "لطفاً بفرمایید دلیل شما برای مراجعه به درمانگری چیست؟",
    "آیا قبلاً تجربه‌ای از مراجعه به درمانگری دارید؟",
    "چه احساساتی در این روزها بیشتر با آنها دست و پنجه نرم می‌کنید؟",
    "آیا در زندگی، حمایت‌هایی از خانواده یا دوستان خود دارید؟",
    "آیا به چیز خاصی فکر می‌کنید که می‌خواهید در این جلسه مطرح کنید؟",
    "با چه چالش‌هایی در زندگی خود مواجه هستید که برای شما سخت است؟",
]

# Create the database to store responses
def create_database():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            user_id INTEGER,
            question_index INTEGER,
            response TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to save a user's response
def save_response(user_id, question_index, response):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO responses (user_id, question_index, response) VALUES (?, ?, ?)', 
                   (user_id, question_index, response))
    conn.commit()
    conn.close()

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    context.user_data['question_index'] = 0  # Initialize question index
    context.user_data['user_id'] = user_id  # Store user ID
    
    # Create a button for starting the process
    keyboard = [[KeyboardButton("شروع")]]  # Creating the "Start" button
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "سلام! خوش آمدید به ربات مشاوره. برای شروع، بر روی 'شروع' کلیک کنید.",
        reply_markup=reply_markup
    )

# Function to handle user responses
async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = context.user_data.get('user_id')  # Get the user ID
    question_index = context.user_data.get('question_index', 0)  # Get the current question index

    # If the user presses "شروع", handle it accordingly
    if update.message.text == "شروع":
        await ask_question(update, context)
    elif question_index < len(questions):
        response = update.message.text
        # Save user response
        save_response(user_id, question_index, response)
        question_index += 1
        context.user_data['question_index'] = question_index
        
        # Ask the next question
        await ask_question(update, context)
    else:
        await update.message.reply_text("شما به همه سوالات پاسخ داده‌اید.")

# Function to send the current question
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question_index = context.user_data.get('question_index', 0)
    if question_index < len(questions):
        await update.message.reply_text(questions[question_index])
    else:
        await update.message.reply_text("شما به همه سوالات پاسخ داده‌اید.")

# Admin command to view all responses
async def view_responses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("شما مجاز به دیدن این اطلاعات نیستید.")
        return

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id, question_index, response FROM responses')
    rows = cursor.fetchall()
    conn.close()

    if rows:
        response_text = "\n".join([f"User ID: {row[0]}, Question Index: {row[1]}, Response: {row[2]}" for row in rows])
        await update.message.reply_text(response_text)
    else:
        await update.message.reply_text("هیچ پاسخی یافت نشد.")

# Entry point for the bot
async def main():
    # Create database
    create_database()
    
    # Create the Application and pass it your bot's token
    application = ApplicationBuilder().token("7866183170:AAGmCn1ULVfG00tZI0egzcUKEMvsshuxZTE").build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))  # Add the start command
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))

    # Run the bot until you stop it
    logger.info("Bot is starting...")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())