from .rzut_cart import RzutCart


def cart_count(request):
    cart = request.session.get("cart", {})
    count = sum(item["quantity"] for item in cart.values())
    rzut_count = RzutCart.count_from_session(request.session)
    return {"cart_count": count, "rzut_cart_count": rzut_count}
