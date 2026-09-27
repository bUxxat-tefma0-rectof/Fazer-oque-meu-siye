from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_LINK, SUPPORT_LINK

def gate_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ ENTRAR NO CANAL", url=CHANNEL_LINK)],
    ])

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Comprar Produtos",  callback_data="menu:catalog")],
        [InlineKeyboardButton(text="🛒 Abrir Loja",        callback_data="menu:shop")],
        [InlineKeyboardButton(text="👤 Meu Perfil",        callback_data="menu:profile")],
        [InlineKeyboardButton(text="💠 Recarregar Saldo",  callback_data="menu:topup")],
        [InlineKeyboardButton(text="👥 Afiliados",         callback_data="menu:affiliates")],
        [InlineKeyboardButton(text="🏆 Top Compradores",   callback_data="menu:ranking")],
        [InlineKeyboardButton(text="📩 Atendimento",       url=SUPPORT_LINK)],
        [InlineKeyboardButton(text="🤖 Sobre o Bot",       callback_data="menu:about")],
        [InlineKeyboardButton(text="🔎 Pesquisar Serviços",callback_data="menu:search")],
    ])
