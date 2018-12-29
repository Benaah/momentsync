from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from channels.auth import AuthMiddlewareStack
from django.conf.urls import url

from moments.consumer import ImageUpdateConsumer


application = ProtocolTypeRouter({
    # (http->django views is added by default)
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                [
                    url(r'^moments/(?P<momentID>[\w-]+)/$', ImageUpdateConsumer),
                ]
            )
        )
    )
})