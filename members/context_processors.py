from django.conf import settings

def liff_and_order(request):
    return {
        "liff_id": getattr(settings, "LINE_LIFF_ID", ""),
        "ICHEF_ORDER_URL": getattr(settings, "ICHEF_ORDER_URL",
                                   "https://shop.ichefpos.com/store/Al0mfcsy/ordering"),
    }

