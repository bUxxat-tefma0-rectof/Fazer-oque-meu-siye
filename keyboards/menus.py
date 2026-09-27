from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_LINK, SUPPORT_LINK


# ---------- GATE ----------

def gate_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ ENTRAR NO CANAL", url=CHANNEL_LINK)],
    ])


# ---------- MENU PRINCIPAL ----------

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Comprar Produtos",   callback_data="menu:catalog")],
        [InlineKeyboardButton(text="🛒 Abrir Loja",         callback_data="menu:shop")],
        [InlineKeyboardButton(text="👤 Meu Perfil",         callback_data="menu:profile")],
        [InlineKeyboardButton(text="💠 Recarregar Saldo",   callback_data="menu:topup")],
        [InlineKeyboardButton(text="👥 Afiliados",          callback_data="menu:affiliates")],
        [InlineKeyboardButton(text="🏆 Top Compradores",    callback_data="menu:ranking")],
        [InlineKeyboardButton(text="📩 Atendimento",        url=SUPPORT_LINK)],
        [InlineKeyboardButton(text="🤖 Sobre o Bot",        callback_data="menu:about")],
        [InlineKeyboardButton(text="🔎 Pesquisar Serviços", callback_data="menu:search")],
    ])


# ---------- CATÁLOGO ----------

def catalog_kb(products) -> InlineKeyboardMarkup:
    rows = []
    for p in products:
        label = f"{p['name']} — R$ {p['price']:.2f}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"prod:{p['id']}")])
    rows.append([InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="nav:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------- PRODUTO ----------

def product_kb(pid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 COMPRAR",             callback_data=f"buy:{pid}:1")],
        [InlineKeyboardButton(text="🛒 Comprar mais de um",  callback_data=f"buy_multi:{pid}")],
        [InlineKeyboardButton(text="⬅️ VOLTAR",              callback_data="menu:catalog")],
    ])


# ---------- SALDO INSUFICIENTE ----------

def insufficient_kb(pid: int, price: float, qty: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💠 Gerar PIX de R$ {price:.2f}", callback_data=f"pix:{pid}:{qty}")],
        [InlineKeyboardButton(text="❌ Cancelar",                      callback_data="nav:home")],
    ])


# ---------- PIX (compra) ----------

def pix_kb(txid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Copiar PIX",             callback_data=f"pixcopy:{txid}")],
        [InlineKeyboardButton(text="⏰ AGUARDANDO PAGAMENTO",   callback_data=f"pixcheck:{txid}")],
        [InlineKeyboardButton(text="❌ Cancelar",               callback_data="nav:home")],
    ])


# ---------- ENTREGA ----------

def delivered_kb(purchase_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔓 VER PRODUTO",                callback_data=f"reveal:{purchase_id}")],
        [InlineKeyboardButton(text="🔗 CLIQUE AQUI PARA ATIVAR",    callback_data=f"activate:{purchase_id}")],
        [InlineKeyboardButton(text="⬅️ VOLTAR",                     callback_data="nav:home")],
    ])


def revealed_kb(purchase_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 CLIQUE AQUI PARA ATIVAR", callback_data=f"activate:{purchase_id}")],
        [InlineKeyboardButton(text="⬅️ VOLTAR",                  callback_data="nav:home")],
    ])


# ---------- COMPRA MÚLTIPLA ----------

def multi_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="nav:home")],
    ])


# ---------- PERFIL ----------

def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Histórico de Compras", callback_data="profile:history:0")],
        [InlineKeyboardButton(text="🎁 Resgatar Gift Card",   callback_data="profile:gift")],
        [InlineKeyboardButton(text="✏️ Alterar dados",        callback_data="profile:edit")],
        [InlineKeyboardButton(text="⬅️ VOLTAR",               callback_data="nav:home")],
    ])


# ---------- HISTÓRICO ----------

def history_empty_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Apenas Ativas", callback_data="profile:history:1")],
        [InlineKeyboardButton(text="⬅️ VOLTAR",        callback_data="menu:profile")],
    ])


def history_active_empty_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Ver Todas", callback_data="profile:history:0")],
        [InlineKeyboardButton(text="⬅️ VOLTAR",    callback_data="menu:profile")],
    ])


def history_kb(purchase_id: str, page: int, total_pages: int, only_active: bool) -> InlineKeyboardMarkup:
    rows = []
    rows.append([InlineKeyboardButton(text="🔗 CLIQUE AQUI PARA ATIVAR",
                                      callback_data=f"activate:{purchase_id}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="⏪ Voltar",
            callback_data=f"profile:hist:{1 if only_active else 0}:{page-1}:{purchase_id}"))
    nav.append(InlineKeyboardButton(text=f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(
            text="⏩ Avançar >>",
            callback_data=f"profile:hist:{1 if only_active else 0}:{page+1}:{purchase_id}"))
    if nav:
        rows.append(nav)
    if only_active:
        rows.append([InlineKeyboardButton(text="📋 Ver Todas", callback_data="profile:history:0")])
    else:
        rows.append([InlineKeyboardButton(text="🟢 Apenas Ativas", callback_data="profile:history:1")])
    rows.append([InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu:profile")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------- GIFT ----------

def gift_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="menu:profile")],
    ])


def gift_use_kb(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Usar", callback_data=f"prod:{product_id}")],
        [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu:profile")],
    ])


# ---------- ALTERAR DADOS ----------

def edit_data_kb(whatsapp: str = None) -> InlineKeyboardMarkup:
    label = f"📱 WhatsApp: {whatsapp}" if whatsapp else "📱 WhatsApp: (não cadastrado)"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data="edit:whatsapp")],
        [InlineKeyboardButton(text="⬅️ Voltar", callback_data="menu:profile")],
    ])


# ---------- RECARGA ----------

def topup_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💠 PIX RÁPIDO", callback_data="topup:pix")],
        [InlineKeyboardButton(text="⬅️ VOLTAR",    callback_data="nav:home")],
    ])


def topup_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="nav:home")],
    ])


def topup_pix_kb(txid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Copiar PIX",           callback_data=f"topupcopy:{txid}")],
        [InlineKeyboardButton(text="⏰ AGUARDANDO PAGAMENTO", callback_data=f"topupcheck:{txid}")],
        [InlineKeyboardButton(text="❌ Cancelar",             callback_data="nav:home")],
    ])


def topup_done_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Comprar",  callback_data="menu:catalog")],
        [InlineKeyboardButton(text="⬅️ VOLTAR",  callback_data="nav:home")],
    ])
