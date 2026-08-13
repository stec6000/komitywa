# Rozdzielenie Produktu, Pozycji Rzutu i Pozycji Zamówienia

Domena zamówień rozdziela katalogowy, wielokrotnie używany **Produkt** od **Pozycji Rzutu** oferowanej w jednym konkretnym Rzucie oraz od niezmiennej **Pozycji Zamówienia** zapisywanej po potwierdzeniu Zamówienia Rzutu. Produkt przechowuje wspólne dane opisowe i wartości domyślne, Pozycja Rzutu — cenę, Porcję, Pulę i limit Klienta właściwe dla danego Rzutu, a Pozycja Zamówienia — nazwę, cenę, Porcję i ilość z chwili zakupu. Pozwala to ponownie wykorzystywać katalog bez przepisywania historii po późniejszej zmianie Produktu lub oferty.

## Rozważone możliwości

- Bezpośrednie użycie Produktu jako oferty wiązałoby dane katalogowe z ceną i Dostępnością właściwą dla jednego Rzutu.
- Tworzenie nowego Produktu w każdym Rzucie powielałoby opisy i zdjęcia oraz utrudniałoby zarządzanie powracającymi Produktami.
- Zachowanie historii wyłącznie w obecnym JSON-ie koszyka nie utrwala wystarczających danych i utrudnia wiarygodne raportowanie.
