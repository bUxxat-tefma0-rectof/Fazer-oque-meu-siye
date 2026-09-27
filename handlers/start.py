from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated
from aiogram.exceptions import TelegramBadRequest

from config import CHANNEL_ID, BANNER_URL
from database import ensure_user, get_user, get_balance, set_gate_message, get_gate_message
from keyboards.menus import gate_kb, main_menu_kb

router = Router()

GATE_TEXT = (
    "❗ Para utilizar nosso serviço é obrigatório que você entre no nosso grupo."
)


def welcome_text(user_id: int, balance: float) -> str:
    return (
        "📡 <b>Bem-vindo à Larizinha Store!</b>\n"
        "✨ A sua central de streamings com entrega 100% automática.\n"
        "Pagou, recebeu. Sem filas, sem precisar falar com atendente, 24 horas por dia! ⚡\n\n"
        "🛡 <b>Segurança e Suporte:</b>\n"
        "Mais de 12.000 clientes já passaram por aqui.\n"
        "Participe da nossa comunidade e veja as referências\n\n"
        "● <b>Seus Dados:</b>\n"
        f"├ 👤 ID: <code>{user_id}</code>\n"
        f"└ 💰 Saldo Atual: R$ {balance:.2f}\n\n"
        "👇 <b>COMO COMEÇAR:</b>\n"
        'Clique no botão "🛍 Comprar Produtos" abaixo para ver nosso catálogo e escolher sua tela!'
    )


async def is_member(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


async def safe_edit(message: Message, text: str, kb=None):
    try:
        if message.photo:
            await message.edit_caption(caption=text, reply_markup=kb)
        else:
            await message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        pass


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)
    ref_by = None
    if len(args) > 1 and args[1].startswith("ref"):
        try:
            ref_by = int(args[1][3:])
        except ValueError:
            ref_by = None

    await ensure_user(user_id, message.from_user.username, message.from_user.first_name, ref_by)

    # 1) Gate
    if not await is_member(bot, user_id):
        sent = await message.answer(GATE_TEXT, reply_markup=gate_kb())
        await set_gate_message(user_id, sent.message_id)
        return

    # 2) Boas-vindas
    balance = await get_balance(user_id)
    text = welcome_text(user_id, balance)

    if BANNER_URL:
        await message.answer_photo(BANNER_URL, caption=text, reply_markup=main_menu_kb())
    else:
        await message.answer(text, reply_markup=main_menu_kb())


# Detecção automática de entrada no canal
@router.ch
at_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_join_channel(event: ChatMemberUpdated, bot: Bot):
    if str(event.chat.id) != str(CHANNEL_ID) and event.chat.username != str(CHANNEL_ID).lstrip("@"):
        return

    user_id = event.from_user.id
    msg_id = await get_gate_message(user_id)
    if not msg_id:
        return

    balance = await get_balance(user_id)
    text = welcome_text(user_id, balance)

    try:
        if BANNER_URL:
            await bot.edit_message_caption(
                chat_id=user_id, message_id=msg_id,
                caption=text, reply_markup=main_menu_kb(),
            )
        else:
            await bot.edit_message_text(
                chat_id=user_id, message_id=msg_id,
                text=text, reply_markup=main_menu_kb(),
            )
    except TelegramBadRequest:
        pass


# Fallback dos botões do menu — módulos seguintes vão substituir cada um
@router.callback_query(F.data.startswith("menu:"))
async def menu_router(cb: CallbackQuery):
    await cb.answer("Em construção 🚧", show_alert=False)
