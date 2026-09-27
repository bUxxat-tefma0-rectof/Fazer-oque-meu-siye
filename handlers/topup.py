import uuid
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ForceReply
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (get_balance, add_balance, create_payment, get_payment,
                      mark_payment_paid)
from keyboards.menus import (topup_kb, topup_cancel_kb, topup_pix_kb, topup_done_kb)
from handlers.catalog import safe_edit

router = Router()

MIN_TOPUP = 4.00
BONUS_MIN = 10.00
BONUS_PCT = 0.10


class TopUp(StatesGroup):
    amount = State()


TOPUP_INTRO = (
    "💠 Opte por PIX Rápido para que seu saldo seja creditado imediatamente.\n"
    "💰 Selecione uma opção para recarregar:"
)

TOPUP_ASK = (
    "ℹ️ Informe o valor que deseja recarregar:\n"
    f"🔻 Recarga mínima: R$ {MIN_TOPUP:.2f}\n"
    "⚠️ Por favor, envie o valor que deseja recarregar agora.\n"
    "Ao realizar um depósito você declara ter lido e estar de acordo com nossos /termos\n"
    f"🎁 Bônus de recarga: {int(BONUS_PCT*100)}%\n"
    f"❗ Recarga mínima para ganhar o bônus: R$ {BONUS_MIN:.2f}"
)


def _pix_text(txid: str, amount: float, bonus: float, current: float) -> str:
    after = current + amount + bonus
    return (
        "💠 <b>Pagamento PIX gerado</b>\n"
        "────────────\n"
        "Escaneie o QR Code abaixo:\n\n"
        f"💵 Valor: R$ {amount:.2f}\n"
        f"🆔 ID da recarga: <code>{txid}</code>\n"
        f"💰 Saldo Atual: R$ {current:.2f}\n"
        f"🎁 Bônus à receber: R$ {bonus:.2f}\n"
        f"💸 Saldo após o pagamento: R$ {after:.2f}\n"
        "⏰ Tempo de expiração: 10 minutos"
    )


@router.callback_query(F.data == "menu:topup")
async def open_topup(cb: CallbackQuery):
    await safe_edit(cb.message, TOPUP_INTRO, topup_kb())
    await cb.answer()


@router.callback_query(F.data == "topup:pix")
async def ask_amount(cb: CallbackQuery, state: FSMContext):
    await state.set_state(TopUp.amount)
    await safe_edit(cb.message, TOPUP_ASK, topup_cancel_kb())
    await cb.message.answer(
        "Digite o valor abaixo:",
        reply_markup=ForceReply(selective=True),
    )
    await cb.answer()


@router.message(TopUp.amount)
async def receive_amount(message: Message, state: FSMContext):
    text = (message.text or "").strip().replace(",", ".")
    if text == "/start":
        await message.answer(
            "⚠️ Você está em um fluxo de recarga. Envie o valor ou cancele.",
            reply_markup=ForceReply(selective=True),
        )
        return
    try:
        amount = float(text)
    except ValueError:
        await message.answer(
            "❌ Valor inválido. Envie apenas números. Ex: <code>20</code>",
            reply_markup=ForceReply(selective=True),
        )
        return
    if amount < MIN_TOPUP:
        await message.answer(
            f"❌ Recarga mínima é R$ {MIN_TOPUP:.2f}. Envie outro valor.",
            reply_markup=ForceReply(selective=True),
        )
        return

    await state.clear()

    user_id = message.from_user.id
    bonus = round(amount * BONUS_PCT, 2) if amount >= BONUS_MIN else 0.0
    current = await get_balance(user_id)
    txid = str(uuid.uuid4())

    await create_payment(txid, user_id, amount, "topup", bonus=bonus)

    sent = await message.answer("⏳ Gerando pagamento...")
    await sent.edit_text(_pix_text(txid, amount, bonus, current), reply_markup=topup_pix_kb(txid))


@router.callback_query(F.data.startswith("topupcopy:"))
async def copy_pix(cb: CallbackQuery):
    await cb.answer("Código PIX copiado! ✅", show_alert=False)


@router.callback_query(F.data.startswith("topupcheck:"))
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
            topup_pix_kb(txid),
        )
        await cb.answer()
        return

    # credita saldo + bônus
    total_credit = float(pay["amount"]) + float(pay["bonus"] or 0)
    await add_balance(cb.from_user.id, total_credit)

    await safe_edit(
        cb.message,
        "✅ <b>Recarga realizada com sucesso!</b>\n"
        f"💰 Valor creditado: R$ {float(pay['amount']):.2f}\n"
        f"🎁 Bônus recebido: R$ {float(pay['bonus'] or 0):.2f}\n"
        f"💸 Saldo atual: R$ {await get_balance(cb.from_user.id):.2f}",
        topup_done_kb(),
    )
    await cb.answer("✅ Recarga confirmada!")


# Admin confirma pagamento: /pagar <txid> (mesmo comando do módulo 2)
