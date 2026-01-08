
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_shopify': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': str(BASE_DIR.parent / 'logs/shopify.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'business.shopify_orders': {
            'handlers': ['file_shopify'],
            'level': 'INFO',
            'propagate': True,
        },
        'business.shopify_products': {
            'handlers': ['file_shopify'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
