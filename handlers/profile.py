from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ForceReply
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from database import (get_user, get_balance, get_user_stats, list_purchases,
                      get_gift, use_gift, add_balance, update_whatsapp,
                      get_product)
from keyboards.menus import (profile_kb, history_empty_kb, history_active_empty_kb,
                             history_kb, gift_cancel_kb, gift_use_kb, edit_data_kb)
from handlers.catalog import safe_edit

router = Router()


class GiftState(StatesGroup):
    code = State()


class EditState(StatesGroup):
    whatsapp = State()


def profile_text(user, stats, balance: float) -> str:
    wa = user["whatsapp"] or "—"
    return (
        "👤 <b>Meu perfil</b>\n"
        "🔍 Veja aqui os detalhes da sua conta:\n"
        "- 👤 <b>Informações:</b>\n"
        f"🆔 ID da Carteira: <code>{user['user_id']}</code>\n"
        f"💰 Saldo Atual: R$ {balance:.2f}\n"
        f"📲 Seu Whatsapp: {wa}\n"
        "─── 📊 <b>Suas Movimentações:</b>\n"
        f"ー 🛒 Compras Realizadas: {stats['compras']}\n"
        f"ー 💰 Total Gasto Em Compras: R$ {stats['gasto']:.2f}\n"
        f"ー 💠 Pix Inseridos: R$ {stats['pix']:.2f}\n"
        f"ー 🎁 Gifts Resgatados: R$ {stats['gifts']:.2f}"
    )


@router.callback_query(F.data == "menu:profile")
async def open_profile(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    if not user:
        await cb.answer("Usuário não encontrado", show_alert=True)
        return
    balance = await get_balance(cb.from_user.id)
    stats = await get_user_stats(cb.from_user.id)
    await safe_edit(cb.message, profile_text(user, stats, balance), profile_kb())
    await cb.answer()


# ---------- HISTÓRICO ----------

def _history_item_text(p) -> str:
    email = "N/A"
    senha = "N/A"
    return (
        f"⏰ Data da compra: {p['created_at']}\n"
        f"📆 Vencimento: {p['expires_at']}\n"
        f"💰 Valor: R$ {p['price']:.2f}\n"
        f"🎫 ID da compra: <code>{p['purchase_id']}</code>\n"
        f"⚜️ Serviço: {p['product_name']} (no seu email)\n"
        f"📧 Email: {email}\n"
        f"🔐 Senha: {senha}\nn"
        "📃 <b"
>Nota:</b> Use o link abaixo para at       ivar:"
    )


 "@router.callback_query(F.data.startswith("profileEx:history:"))
async def open_history(cb: CallbackQuery):
    only_active = cb.data.split(":")[2] == "1"
    items = await list_purchases(cb.from_user.id, only_active=only_active)

    if not items:
        if only_active:
            await safe_edit(
                cb.message,
                "Você não tem compras ativas (não vencidas) no bot.",
                history_active_empty_kb(),
            )
        else:
            await safe_edit(
                cb.message,
                "Você não tem compras no bot.\n"
                "Quando comprar alguma conta, as informações dela ficarão exibidas aqui.",
                history_empty_kb(),
            )
        await cb.answer()
        return

    total_pages = len(items)
    text =emplo f"📦 Compras: {len(items)}\n\n" + _history_item_text(items[0])
    await safe_edit(cb.message, text, history_kb(items[0]["purchase_id"], 0, total_pages, only_active))
    await cb.answer()


@router.callback_query(F.data.startswith("profile:hist:"))
async def history_page(cb: CallbackQuery):
    _, _, active_s, page_s, purchase_id = cb.data.split(":")
    only_active = active_s == "1"
    page = int(page_s)
    items = await list_purchases(cb.from_user.id, only_active=only_active)
    if not items:
        await cb.answer("Sem compras", show_alert=True)
        return
    page = max(0, min(page, len(items) - 1))
    text = f"📦 Compras: {len(items)}\n\n" + _history_item_text(items[page])
    await safe_edit(cb.message, text, history_kb(items[page]["purchase_id"], page, len(items), only_active))
    await cb.answer()


@router.callback_query(F.data == "noop")
async def noop(cb: CallbackQuery):
    await cb.answer()


# ---------- GIFT CARD ----------

@router.callback_query(F.data == "profile:gift")
async def open_gift(cb: CallbackQuery, state: FSMContext):
    await state.set_state(GiftState.code)
    await safe_edit(
        cb.message,
        "🎁 <b>RESGATAR GIFT CARD</b>\n"
        "Digite o código do seu gift card abaixo:\: <code>ABC123XYZ456</code>",
        gift_cancel_kb(),
    )
    await cb.answer()


@router.message(GiftState.code)
async def receive_gift(message: Message, state: FSMContext):
    code = (message.text or "").strip()
    if not code:
        await message.answer("❌ Código inválido.")
        return
    gift = await get_gift(code)
    if not gift or gift["used"]:
        await state.clear()
        await message.answer("Gift não encontrado.", reply_markup=gift_cancel_kb())
        return

    await use_gift(code, message.from_user.id)
    await state.clear()

    if gift["product_id"]:
        p = await get_product(gift["product_id"])
        text = (
            "🎁 <b>Gift Card resgatado!</b>\n"
            f"⚜️ Produto liberado: {p['name'] if p else '—'}\n"
            "Toque em <b>Usar</b> para abrir o produto direto."
        )
        await message.answer(text, reply_markup=gift_use_kb(gift["product_id"]))
    else:
        await add_balance(message.from_user.id, float(gift["value"] or 0))
        await message.answer(
            "🎁 <b>Gift Card resgatado!</b>\n"
            f"💰 Valor creditado: R$ {float(gift['value'] or 0):.2f}",
            reply_markup=gift_cancel_kb(),
        )


# ---------- ALTERAR DADOS ----------

@router.callback_query(F.data == "profile:edit")
async def open_edit(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    await safe_edit(
        cb.message,
        "✏️ <b>Alterar Dados</b>\nSelecione o dado que deseja alterar:",
        edit_data_kb(user["whatsapp"] if user else None),
    )
    await cb.answer()


@router.callback_query(F.data == "edit:whatsapp")
async def ask_whatsapp(cb: CallbackQuery, state: FSMContext):
    await state.set_state(EditState.whatsapp)
    await safe_edit(
        cb.message,
        "📱 <b>Envie seu número de WhatsApp</b>\n"
        "Formato: DDD + Número (apenas números)\n"
        "Exemplo: <code>11999998888</code>\n"
        '⚠️ Envie "remover" para remover o número cadastrado.',
        None,
    )
    await cb.message.answer(
        "Digite abaixo:",
        reply_markup=ForceReply(selective=True),
    )
    await cb.answer()


@router.message(EditState.whatsapp)
async def receive_whatsapp(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == "/start":
        await message.answer(
            "⚠️ Você está em um fluxo de alteração. Envie um número válido ou 'remover'.",
            reply_markup=ForceReply(selective=True),
        )
        return
    if text.lower() == "remover":
        await update_whatsapp(message.from_user.id, None)
        await state.clear()
        await message.answer("✅ WhatsApp removido com sucesso.")
        return
    if not text.isdigit() or not (10 <= len(text) <= 11):
        await message.answer(
            "❌ <b>Número inválido!</b>\n"
            "Formato: DDD + Número (apenas números). Exemplo: <code>11999998888</code>",
            reply_markup=ForceReply(selective=True),
        )
        return
    await update_whatsapp(message.from_user.id, text)
    await state.clear()
    await message.answer(f"✅ WhatsApp atualizado com sucesso!\n📱 {text}")
