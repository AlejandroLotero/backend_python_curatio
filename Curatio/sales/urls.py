# from django.urls import path

# from . import api_views

# urlpatterns = [
#     # =========================
#     # SPA / V1 - SALES
#     # =========================

#     # Listado y creación de ventas
#     path("v1/sales/", api_views.sales_resource, name="sales_resource"),

#     # Detalle y actualización de venta
#     path("v1/sales/<int:sale_id>/", api_views.sale_detail_resource, name="sale_detail_resource"),

#     # Confirmación de pago
#     path(
#         "v1/sales/<int:sale_id>/confirm-payment/",
#         api_views.sale_confirm_payment_resource,
#         name="sale_confirm_payment_resource",
#     ),

#     # Anulación de venta
#     path(
#         "v1/sales/<int:sale_id>/cancel/",
#         api_views.sale_cancel_resource,
#         name="sale_cancel_resource",
#     ),

#     # Reportes Excel / PDF
#     path("v1/sales/reports/", api_views.sales_report_resource, name="sales_report_resource"),

#     # Factura / comprobante individual
#     path("v1/sales/<int:sale_id>/invoice/", api_views.sale_invoice_resource, name="sale_invoice_resource"),

#     path(
#     "v1/sales/catalogs/customers/",
#     api_views.sales_customers_catalog_resource,
#     name="sales_customers_catalog_resource",
#     ),
#     path(
#     "v1/sales/web-checkout/",
#     api_views.customer_checkout_resource,
#     name="customer_checkout_resource",
#     ),
#     path(
#     "v1/sales/catalogs/customers/lookup/",
#     api_views.sales_customer_lookup_resource,
#     name="sales_customer_lookup_resource",
#     ),
# ]

from django.urls import path
from . import api_views

urlpatterns = [
    path("v1/sales/", api_views.sales_resource, name="sales_resource"),
    path("v1/sales/<int:sale_id>/", api_views.sale_detail_resource, name="sale_detail_resource"),
    path("v1/sales/<int:sale_id>/confirm-payment/", api_views.sale_confirm_payment_resource, name="sale_confirm_payment_resource"),
    path("v1/sales/<int:sale_id>/cancel/", api_views.sale_cancel_resource, name="sale_cancel_resource"),
    path("v1/sales/<int:sale_id>/invoice/", api_views.sale_invoice_resource, name="sale_invoice_resource"),

    # =========================
    # CHECKOUT WEB
    # =========================
    path("v1/sales/web-checkout/", api_views.customer_checkout_resource, name="customer_checkout_resource"),
    path("v1/sales/<int:sale_id>/approve-internal/", api_views.sale_internal_approval_resource, name="sale_internal_approval_resource"),

    # =========================
    # NOTIFICACIONES
    # =========================
    path("v1/sales/notifications/", api_views.sales_notifications_resource, name="sales_notifications_resource"),
    path("v1/sales/notifications/<int:notification_id>/read/", api_views.sales_notification_read_resource, name="sales_notification_read_resource"),

    # =========================
    # CATÁLOGOS
    # =========================
    path("v1/sales/catalogs/customers/", api_views.sales_customers_catalog_resource, name="sales_customers_catalog_resource"),
    path("v1/sales/catalogs/customers/lookup/", api_views.sales_customer_lookup_resource, name="sales_customer_lookup_resource"),
]