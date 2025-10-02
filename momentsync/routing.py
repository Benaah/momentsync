from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack
from django.urls import re_path

from websocket.consumers import MomentConsumer


application = ProtocolTypeRouter({
    # (http->django views is added by default)
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                [
                    re_path(r'^ws/moments/(?P<momentID>[\w-]+)/$', MomentConsumer),
                ]
            )
        )
    )
})