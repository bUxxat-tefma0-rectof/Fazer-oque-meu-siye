from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from database import (get_balance, list_products, get_product,
                      get_user, create_purchase, sub_balance)
from keyboards.menus import (catalog_kb, product_kb, insufficient_kb,
                             multi_cancel_kb, delivered_kb, revealed_kb)

router = Router()
PRODUCTS_PER_PAGE = 10


class MultiBuy(StatesGroup):
    qty = State()


async def safe_edit(msg: Message, text: str, kb=None):
    try:
        if msg.photo:
            await msg.edit_caption(caption=text, reply_markup=kb)
        else:
            await msg.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        pass


def catalog_text(balance: float) -> str:
    return (
        "⚡ <b>Lari Contas | Catálogo de Serviços</b>\n"
        "────────────────────────\n"
        f"💰 | Saldo da Carteira: R$ {balance:.2f}\n"
        "⬇️ Selecione uma categoria abaixo para ver nossos planos:"
    )


def product_text(p, balance: float) -> str:
    stock_txt = f"{p['stock']}" if p['stock'] > 0 else "0"
    desc = (p['description'] or "LEIA A DESCRIÇÃO DO PRODUTO").strip()
    guarantee = p['guarantee'] or "180 dias"
    old_line = ""
    if p['old_price']:
        old_line = f"<s>R$ {p['old_price']:.2f}</s> → "
    return (
        "🔥 <b>OPORTUNIDADE EXCLUSIVA</b> 🔥\n"
        f"🚀 <b>{p['name']}</b>\n"
        "🟢 DISPONÍVEL AGORA\n"
        f"├ 💵 Preço: R$ {p['price']:.2f}\n"
        f"├ 💰 Seu Saldo: R$ {balance:.2f}\n"
        f"└ 📦 Estoque: {stock_txt}\n"
        "📝 <b>Descrição:</b>\n"
        f"{desc}\n"
        "📊 <b>Estatísticas em tempo real:</b>\n"
        f"⚡️ Já foram vendidas {p['sold']} unidades!\n"
        "👀 14 pessoas estão vendo isso agora.\n"
        f"🛡 Garantia: {guarantee}\n"
        "✅ Compra segura. Ao adquirir, concorda com /termos"
    )


@router.callback_query(F.data == "menu:catalog")
async def open_catalog(cb: CallbackQuery):
    products = await list_products()
    balance = await get_balance(cb.from_user.id)
    await safe_edit(cb.message, catalog_text(balance), catalog_kb(products))
    await cb.answer()


@router.callback_query(F.data.startswith("prod:"))
async def open_product(cb: CallbackQuery):
    pid = int(cb.data.split(":")[1])
    p = await get_product(pid)
    if not p:
        await cb.answer("Produto não encontrado", show_alert=True)
        return
    balance = await get_balance(cb.from_user.id)
    await safe_edit(cb.message, product_text(p, balance), product_kb(pid))
    await cb.answer()


@router.callback_query(F.data.startswith("buy:"))
async def buy_single(cb: CallbackQuery):
    _, pid_s, qty_s = cb.data.split(":")
    pid, qty = int(pid_s), int(qty_s)
    await _process_buy(cb, pid, qty)


@router.callback_query(F.data.startswith("buy_multi:"))
async def buy_multi(cb: CallbackQuery, state: FSMContext):
    pid = int(cb.data.split(":")[1])
    p = await get_product(pid)
    if not p:
        await cb.answer("Produto não encontrado", show_alert=True)
        return
    await state.update_data(pid=pid)
    await state.set_state(MultiBuy.qty)
    text = (
        "Quantos logins deseja comprar?\n"
        f"📦 Estoque disponível: {p['stock']}\n"
        "💡 Digite /cancelar a qualquer momento para sair."
    )
    await safe_edit(cb.message, text, multi_cancel_kb())
    await cb.answer()


@router.message(MultiBuy.qty)
async def multi_qty_input(message: Message, state: FSMContext):
    if message.text and message.text.strip() == "/cancelar":
        await state.clear()
        await message.answer("❌ <b>Compra cancelada!</b>\nOperação de compra múltipla foi cancelada.")
        return
    if not message.text or not message.text.strip().isdigit():
        await message.answer("❌ Digite apenas um número válido.")
        return
    qty = int(message.text.strip())
    if qty < 1:
        await message.answer("❌ Quantidade inválida.")
        return
    data = await state.get_data()
    pid = data.get("pid")
    await state.clear()
    p = await get_product(pid)
    if not p:
        await message.answer("❌ Produto não encontrado.")
        return
    if qty > p["stock"]:
        await message.answer(f"❌ Estoque insuficiente. Disponível: {p['stock']}")
        return

    user_id = message.from_user.id
    balance = await get_balance(user_id)
    total = p["price"] * qty

    if balance >= total:
        await sub_balance(user_id, total)
        import uuid
        pid_uuid = str(uuid.uuid4())
        await create_purchase(pid_uuid, user_id, p["id"], p["name"], total, qty)
        pur = await create_purchase_return(pid_uuid)
        await message.answer(_delivered_text(pur, p))
    else:
        faltam = total - balance
        text = (
            "❌ <b>Saldo insuficiente!</b>\n"
            f"💰 Seu saldo: R$ {balance:.2f}\n"
            f"💵 Valor do produto: R$ {total:.2f}\n"
            f"📉 Faltam: R$ {faltam:.2f}\n"
            f"💡 Deseja gerar um PIX no valor de R$ {total:.2f} para completar a compra?"
        )
        await message.answer(text, reply_markup=insufficient_kb(pid, total, qty))


async def create_purchase_return(pid_uuid: str):
    from database import get_purchase_by_id
    return await get_purchase_by_id(pid_uuid)


async def _process_buy(cb: CallbackQuery, pid: int, qty: int):
    p = await get_product(pid)
    if not p:
        await cb.answer("Produto não encontrado", show_alert=True)
        return
    user_id = cb.from_user.id
    balance = await get_balance(user_id)
    total = p["price"] * qty

    if p["stock"] < qty:
        await cb.answer("Estoque insuficiente", show_alert=True)
        return

    if balance >= total:
        await sub_balance(user_id, total)
        import uuid
        pid_uuid = str(uuid.uuid4())
        await create_purchase(pid_uuid, user_id, p["id"], p["name"], total, qty)
        pur = await create_purchase_return(pid_uuid)
        await safe_edit(cb.message, _delivered_text(pur, p), delivered_kb(pid_uuid))
        await cb.answer("✅ Compra realizada!")
    else:
        faltam = total - balance
        text = (
            "❌ <b>Saldo insuficiente!</b>\n"
            f"💰 Seu saldo: R$ {balance:.2f}\n"
            f"💵 Valor do produto: R$ {total:.2f}\n"
            f"📉 Faltam: R$ {faltam:.2f}\n"
            f"💡 Deseja gerar um PIX no valor de R$ {total:.2f} para completar a compra?"
        )
        await safe_edit(cb.message, text, insufficient_kb(pid, total, qty))
        await cb.answer()


def _delivered_text(pur, p=None) -> str:
    from datetime import datetime
    created = pur["created_at"] if "created_at" in pur.keys() else ""
    expires = pur["expires_at"] if "expires_at" in pur.keys() else ""
    email = "•" * 16
    senha = "•" * 16
    return (
        "✅ <b>Produto realizado com sucesso!</b>\n"
        f"⏰ Data da compra: {created}\n"
        f"📆 Vencimento: {expires}\n"
        f"💰 Valor: R$ {pur['price']:.2f}\n"
        f"🎫 ID da compra: <code>{pur['purchase_id']}</code>\n"
        f"⚜️ Serviço: {pur['product_name']} (no seu email)\n"
        f"📧 Email: {email}\n"
        f"🔐 Senha: {senha}\n"
        "📃 <b>Nota:</b> Use o botão abaixo para ativar:"
    )


def _revealed_text(pur) -> str:
    email = pur["email"] or "N/A"
    senha = pur["password"] or "N/A"
    return (
        "✅ <b>Produto realizado com sucesso!</b>\n"
        f"⏰ Data da compra: {pur['created_at']}\n"
        f"📆 Vencimento: {pur['expires_at']}\n"
        f"💰 Valor: R$ {pur['price']:.2f}\n"
        f"🎫 ID da compra: <code>{pur['purchase_id']}</code>\n"
        f"⚜️ Serviço: {pur['product_name']} (no seu email)\n"
        f"📧 Email: <code>{email}</code>\n"
        f"🔐 Senha: <code>{senha}</code>\n"
        "📃 <b>Nota:</b> Use o botão abaixo para ativar:"
    )


@router.callback_query(F.data.startswith("reveal:"))
async def reveal_product(cb: CallbackQuery):
    purchase_id = cb.data.split(":", 1)[1]
    from database import get_purchase_by_id
    pur = await get_purchase_by_id(purchase_id)
    if not pur or pur["user_id"] != cb.from_user.id:
        await cb.answer("Acesso negado", show_alert=True)
        return
    await safe_edit(cb.message, _revealed_text(pur), revealed_kb(purchase_id))
    await cb.answer()


@router.callback_query(F.data.startswith("activate:"))
async def activate_product(cb: CallbackQuery):
    await cb.answer("🔗 Link de ativação", url="https://t.me/")


@router.callback_query(F.data == "nav:home")
async def back_home(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    from database import get_balance
    from handlers.start import welcome_text, main_menu_kb
    balance = await get_balance(cb.from_user.id)
    await safe_edit(cb.message, welcome_text(cb.from_user.id, balance), main_menu_kb())
    await cb.answer()
