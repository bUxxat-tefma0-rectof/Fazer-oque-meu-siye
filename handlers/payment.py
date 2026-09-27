import uuid
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from database import (get_balance, get_product, create_payment, get_payment,
                      mark_payment_paid, add_balance, get_user)
from keyboards.menus import pix_kb, delivered_kb
from handlers.catalog import _delivered_text, safe_edit

router = Router()


def _pix_text(txid: str, amount: float) -> str:
    return (
        "💠 <b>Pagamento PIX gerado</b>\n"
        "────────────\n"
        f"💵 Valor: R$ {amount:.2f}\n"
        f"🆔 ID da recarga: <code>{txid}</code>\n"
        "⏰ Tempo de expiração: 10 minutos\n"
        "────────────\n"
        "Escaneie o QR Code ou copie o código abaixo:"
    )


@router.callback_query(F.data.startswith("pix:"))
async def generate_pix(cb: CallbackQuery):
    _, pid_s, qty_s = cb.data.split(":")
    pid, qty = int(pid_s), int(qty_s)
    p = await get_product(pid)
    if not p:
        await cb.answer("Produto não encontrado", show_alert=True)
        return

    total = p["price"] * qty
    txid = str(uuid.uuid4())
    await create_payment(txid, cb.from_user.id, total, "product", product_id=pid, quantity=qty)

    await safe_edit(cb.message, "⏳ Gerando pagamento...")
    await safe_edit(cb.message, _pix_text(txid, total), pix_kb(txid))
    await cb.answer()


@router.callback_query(F.data.startswith("pixcopy:"))
async def copy_pix(cb: CallbackQuery):
    txid = cb.data.split(":", 1)[1]
    await cb.answer("Código PIX copiado! ✅", show_alert=False)


@router.callback_query(F.data.startswith("pixcheck:"))
async def check_pix(cb: CallbackQuery):
    txid = cb.data.split(":", 1)[1]
    pay = await get_payment(txid)
    if not pay:
        await cb.answer("Pagamento não encontrado", show_alert=True)
        return

    if pay["status"] != "paid":
        await safe_edit(
            cb.message,
            "Nosso sistema viu que você não realizou o pagamento.",
            pix_kb(txid),
        )
        await cb.answer()
        return

    # Pagamento confirmado -> entrega
    user_id = pay["user_id"]
    pid = pay["product_id"]
    qty = pay["quantity"]
    p = await get_product(pid)

    from database import create_purchase, get_purchase_by_id
    purchase_uuid = str(uuid.uuid4())
    await create_purchase(purchase_uuid, user_id, p["id"], p["name"], pay["amount"], qty)
    pur = await get_purchase_by_id(purchase_uuid)

    await safe_edit(
        cb.message,
        "✅ <b>PAGO</b>\n\n" + _delivered_text(pur),
        delivered_kb(purchase_uuid),
    )
    await cb.answer("✅ Pagamento confirmado!")


# webhook/confirmação manual do admin: /pagar <txid>
from aiogram.filters import Command
from aiogram.types import Message
from config import ADMIN_IDS


@router.message(Command("pagar"))
async def admin_confirm(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Uso: /pagar <txid>")
        return
    txid = parts[1]
    pay = await get_payment(txid)
    if not pay:
        await message.answer("Pagamento não encontrado.")
        return
    await mark_payment_paid(txid)
    await message.answer(f"✅ Pagamento {txid} marcado como PAGO.")
