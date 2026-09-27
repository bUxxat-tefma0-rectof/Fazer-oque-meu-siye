from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_IDS
from database import add_product, remove_product, list_products, set_product_stock

router = Router()


def _admin_only(msg: Message) -> bool:
    return msg.from_user.id in ADMIN_IDS


@router.message(Command("addprod"))
async def add_prod(message: Message):
    if not _admin_only(message):
        return
    # /addprod code | nome | preço | preço_antigo | estoque | descrição | garantia | categoria
    parts = [p.strip() for p in message.text.split("|")]
    if len(parts) < 6:
        await message.answer(
            "Uso:\n"
            "<code>/addprod code | nome | preço | preço_antigo | estoque | descrição | garantia | categoria</code>\n\n"
            "Exemplo:\n"
            "<code>/addprod canva6 | CANVA PRO (6 MESES) | 18.00 | 25.00 | 3 | Conta privada Canva Education | 180 dias | Streaming</code>"
        )
        return

    _, code, name, price, old, stock, *rest = parts
    desc = rest[0] if len(rest) > 0 else ""
    guarantee = rest[1] if len(rest) > 1 else ""
    category = rest[2] if len(rest) > 2 else ""

    try:
        price_f = float(price)
        old_f = float(old) if old else None
        stock_i = int(stock)
    except ValueError:
        await message.answer("❌ Preço, preço antigo ou estoque inválidos.")
        return

    try:
        await add_product(code, name, price_f, old_f, stock_i, desc, guarantee, category)
    except Exception as e:
        await message.answer(f"❌ Erro ao adicionar: {e}")
        return

    await message.answer(
        f"✅ Produto adicionado!\n"
        f"├ Código: <code>{code}</code>\n"
        f"├ Nome: {name}\n"
        f"├ Preço: R$ {price_f:.2f}\n"
        f"├ Estoque: {stock_i}\n"
        f"└ Categoria: {category or '—'}"
    )


@router.message(Command("delprod"))
async def del_prod(message: Message):
    if not _admin_only(message):
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Uso: <code>/delprod &lt;id&gt;</code>")
        return
    pid = int(parts[1])
    await remove_product(pid)
    await message.answer(f"🗑 Produto #{pid} removido.")


@router.message(Command("stock"))
async def stock_set(message: Message):
    if not _admin_only(message):
        return
    parts = message.text.split()
    if len(parts) < 3 or not parts[1].isdigit() or not parts[2].lstrip("-").isdigit():
        await message.answer("Uso: <code>/stock &lt;id&gt; &lt;qtd&gt;</code>")
        return
    pid, qty = int(parts[1]), int(parts[2])
    await set_product_stock(pid, qty)
    await message.answer(f"✅ Estoque do produto #{pid} atualizado para {qty}.")


@router.message(Command("listprod"))
async def list_prod(message: Message):
    if not _admin_only(message):
        return
    items = await list_products()
    if not items:
        await message.answer("Nenhum produto cadastrado.")
        return
    lines = ["📦 <b>Produtos cadastrados</b>", "────────────"]
    for p in items:
        lines.append(
            f"#{p['id']} • {p['name']}\n"
            f"   💵 R$ {p['price']:.2f}  •  📦 est. {p['stock']}  •  ✅ vendas {p['sold']}"
        )
    await message.answer("\n".join(lines))
