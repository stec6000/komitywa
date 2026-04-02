from decimal import Decimal

from shop.models import Product


CART_SESSION_KEY = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, product, quantity=1):
        product_id = str(product.id)
        if product.type == "ebook":
            self.cart[product_id] = {
                "quantity": 1,
                "price": str(product.price),
            }
        else:
            if product_id in self.cart:
                self.cart[product_id]["quantity"] += quantity
            else:
                self.cart[product_id] = {
                    "quantity": quantity,
                    "price": str(product.price),
                }
        self.save()

    def remove(self, product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def update_quantity(self, product_id, quantity):
        product_id = str(product_id)
        if product_id in self.cart and quantity > 0:
            self.cart[product_id]["quantity"] = quantity
            self.save()

    def save(self):
        self.session[CART_SESSION_KEY] = self.cart
        self.session.modified = True

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item["price"]) * item["quantity"]
            for item in self.cart.values()
        )

    def clear(self):
        del self.session[CART_SESSION_KEY]
        self.cart = {}
        self.session.modified = True

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(
            id__in=product_ids, is_active=True
        )
        products_map = {str(p.id): p for p in products}

        # Remove stale items (inactive or deleted products)
        stale_ids = [
            pid for pid in list(product_ids) if pid not in products_map
        ]
        for pid in stale_ids:
            del self.cart[pid]
        if stale_ids:
            self.save()

        for product_id, item in self.cart.items():
            product = products_map.get(product_id)
            if product:
                yield {
                    "product": product,
                    "quantity": item["quantity"],
                    "price": Decimal(item["price"]),
                    "total_price": Decimal(item["price"])
                    * item["quantity"],
                }
