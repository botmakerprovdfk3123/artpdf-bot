import logging
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import landscape, inch
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
import os

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Steps
ARTIST, TITLE, PRICE, LINK = range(4)

# Page size
WIDTH = 6 * inch
HEIGHT = 5 * inch
PAGESIZE = landscape((WIDTH, HEIGHT))

# Styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Header', fontSize=22, alignment=TA_CENTER, textColor=colors.black))
styles.add(ParagraphStyle(name='Subheader', fontSize=14, alignment=TA_CENTER))
styles.add(ParagraphStyle(name='Field', fontSize=12))
styles.add(ParagraphStyle(name='StyledButton', fontSize=14, textColor=colors.white, backColor=colors.red, alignment=TA_CENTER, spaceBefore=12, spaceAfter=12))
styles.add(ParagraphStyle(name='Thanks', fontSize=10, alignment=TA_CENTER, textColor=colors.grey))

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Bot token from environment

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm your Artfinder Order PDF bot 🎨\n\nSend /generate to start generating your order confirmation.")

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter artist name:")
    return ARTIST

async def artist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['artist'] = update.message.text
    await update.message.reply_text("Enter artwork title:")
    return TITLE

async def title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Enter price (e.g. €1900):")
    return PRICE

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['price'] = update.message.text
    await update.message.reply_text("Enter confirmation link:")
    return LINK

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['link'] = update.message.text
    filename = f"order_{update.message.from_user.id}.pdf"

    doc = BaseDocTemplate(filename, pagesize=PAGESIZE, rightMargin=0, leftMargin=0, topMargin=0, bottomMargin=0)
    frame = Frame(x1=0.5*inch, y1=0.5*inch, width=WIDTH-1*inch, height=HEIGHT-1*inch, showBoundary=0)
    doc.addPageTemplates([PageTemplate(id='Coupon', frames=frame)])

    elements = []
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2.5*inch, height=0.7*inch)
        logo.hAlign = 'CENTER'
        elements.append(logo)

    elements.extend([
        Spacer(1, 12),
        Paragraph("🎨 Artfinder Order Confirmation", styles['Header']),
        Paragraph("Authentic Original Artwork", styles['Subheader']),
        Spacer(1, 6),
        Paragraph(f"<b>Artist:</b> {context.user_data['artist']}", styles['Field']),
        Paragraph(f"<b>Artwork:</b> {context.user_data['title']}", styles['Field']),
        Paragraph(f"<b>Total Amount:</b> {context.user_data['price']}", styles['Field']),
        Spacer(1, 10),
        Paragraph(f"<a href='{context.user_data['link']}'><font color='white'><b>🛒 Confirm Purchase</b></font></a>", styles['StyledButton']),
        Spacer(1, 10),
        Paragraph("Thank you for supporting independent artists!", styles['Thanks'])
    ])

    doc.build(elements)
    with open(filename, 'rb') as f:
        await update.message.reply_document(document=InputFile(f, filename))
    os.remove(filename)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Send /generate to try again.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('generate', generate)],
        states={
            ARTIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, artist)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, link)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
