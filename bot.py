import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

def init_db():
    conn = sqlite3.connect("finanzas.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS movimientos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  tipo TEXT,
                  monto REAL,
                  categoria TEXT,
                  descripcion TEXT,
                  fecha TEXT)''')
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu asistente de finanzas 💰\n\n"
        "Comandos:\n"
        "/gasto 15000 comida almuerzo\n"
        "/ingreso 450000 sueldo\n"
        "/saldo\n"
        "/resumen\n"
        "/ayuda"
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Cómo usar el bot:\n\n"
        "• /gasto 12000 transporte uber\n"
        "• /ingreso 500000 sueldo\n"
        "• /saldo → ver cuánto tienes\n"
        "• /resumen → resumen del mes"
    )

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usa: /gasto 15000 comida almuerzo")
            return

        monto = float(args[0])
        categoria = args[1]
        descripcion = " ".join(args[2:]) if len(args) > 2 else categoria

        user_id = update.effective_user.id
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect("finanzas.db")
        c = conn.cursor()
        c.execute("INSERT INTO movimientos (user_id, tipo, monto, categoria, descripcion, fecha) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, "gasto", monto, categoria, descripcion, fecha))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ Gasto registrado: ${monto:,.0f} en {categoria}")
    except:
        await update.message.reply_text("Error. Ejemplo: /gasto 15000 comida almuerzo")

async def ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("Usa: /ingreso 450000 sueldo")
            return

        monto = float(args[0])
        descripcion = " ".join(args[1:]) if len(args) > 1 else "Ingreso"

        user_id = update.effective_user.id
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect("finanzas.db")
        c = conn.cursor()
        c.execute("INSERT INTO movimientos (user_id, tipo, monto, categoria, descripcion, fecha) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, "ingreso", monto, "ingreso", descripcion, fecha))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ Ingreso registrado: ${monto:,.0f}")
    except:
        await update.message.reply_text("Error. Ejemplo: /ingreso 450000 sueldo")

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("finanzas.db")
    c = conn.cursor()

    c.execute("SELECT SUM(monto) FROM movimientos WHERE user_id=? AND tipo='ingreso'", (user_id,))
    ingresos = c.fetchone()[0] or 0

    c.execute("SELECT SUM(monto) FROM movimientos WHERE user_id=? AND tipo='gasto'", (user_id,))
    gastos = c.fetchone()[0] or 0

    conn.close()

    saldo_actual = ingresos - gastos
    await update.message.reply_text(
        f"💰 Saldo actual: ${saldo_actual:,.0f}\n\n"
        f"Ingresos: ${ingresos:,.0f}\n"
        f"Gastos: ${gastos:,.0f}"
    )

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("finanzas.db")
    c = conn.cursor()

    c.execute("SELECT categoria, SUM(monto) FROM movimientos WHERE user_id=? AND tipo='gasto' GROUP BY categoria", (user_id,))
    resultados = c.fetchall()
    conn.close()

    if not resultados:
        await update.message.reply_text("Aún no tienes gastos registrados.")
        return

    texto = "📊 Gastos por categoría:\n\n"
    for cat, total in resultados:
        texto += f"• {cat}: ${total:,.0f}\n"

    await update.message.reply_text(texto)

def main():
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("ingreso", ingreso))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("resumen", resumen))

    print("Bot iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
