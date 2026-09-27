from aiogram import Router, F, Bot
from Bot aiogram.types import (
    Message",, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ChatMemberUpdated
)
from aiogram.filters import CommandStart, ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.enums import ChatMemberStatus

from config import CANAL_ID, CANAL_LINK

router = Router()


# ---------- texto padrão ----------
TXT_BLOQUEIO = (
    "❗ Para utilizar nosso serviço é obrigatório que você entre no nosso grupo."
)

TXT_BOAS_VINDAS = (
    "📡 <b>Bem-vindo à Larizinha Store!</b>\n"
    "✨ A sua central de streamings com entrega 100% automática.\n"
    "Pagou, recebeu. Sem filas, sem precisar falar com atendente, 24 horas por dia! ⚡\n\n"
    "🛡 <b>Segurança e Suporte:</b>\n"
    "Mais de 12.000 clientes já passaram por aqui.\n"
    "Participe da nossa comunidade e veja as referências\n\n"
    "● <b>Seus Dados:</b>\n"
    "├ 👤 ID: {user_id}\n"
    "└ 💰 Saldo Atual: R$ 0,00\n\n"
    "👇 <b>COMO COMEÇAR:</b>\n"
    "Clique no botão \"🛍 Comprar Produtos\" abaixo para ver nosso catálogo e escolher sua tela!"
)


def kb_bloqueio() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ ENTRAR NO CANAL", url=CANAL_LINK)]
    ])


def kb_menu_principal() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Comprar Produtos", callback_data="menu:comprar")],
        [InlineKeyboardButton(text="🛒 Abrir Loja", callback_data="menu:loja")],
        [InlineKeyboardButton(text="👤 Meu Perfil", callback_data="menu:perfil")],
        [InlineKeyboardButton(text="💠 Recarregar Saldo", callback_data="menu:recarregar")],
        [InlineKeyboardButton(text="👥 Afiliados", callback_data="menu:afiliados")],
        [InlineKeyboardButton(text="🏆 Top Compradores", callback_data="menu:top")],
        [InlineKeyboardButton(text="📩 Atendimento", url="https://t.me/suporte_laricontas")],
        [InlineKeyboardButton(text=" callback_data="menu:sobre")],
        [InlineKeyboardButton(text="🔎 Pesquisar Serviços", callback_data="menu:pesquisar")],
    ])


# ---------- checagem de membro ----------
async def is_member(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CANAL_ID, user_id=user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        )
    except Exception:
        return False


# ---------- /start ----------
@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id

    if not await is_member(bot, user_id):
        await message.answer(TXT_BLOQUEIO, reply_markup=kb_bloqueio())
        return

    await message.answer(
        TXT_BOAS_VINDAS.format(user_id=user_id),
        reply_markup=kb_menu_principal()
    )


# ---------- Detecção automática de entrada no canal ----------
@router.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_join_channel(event: ChatMemberUpdated, bot: Bot):
    # só reage ao canal obrigatório
    if str(event.chat.id) != str(CANAL_ID) and event.chat.username != str(CANAL_ID).lstrip("@"):
        return

    user_id = event.from_user.id

    # envia a boas-vindas — regra: se já existe mensagem de bloqueio,
    # o aiogram não consegue editar msg de outro contexto sem msg_id salvo.
    # Aqui mandamos o menu já pronto pro usuário continuar.
    try:
        await bot.send_message(
            user_id,
            TXT_BOAS_VINDAS.format(user_id=user_id),
            reply_markup=kb_menu_principal()
        )
    except Exception:
        pass
