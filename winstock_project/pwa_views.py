from django.conf import settings
from django.http import FileResponse
from django.views.decorators.cache import never_cache


@never_cache
def service_worker(request):
    """Sirve el Service Worker desde la raíz para habilitar su ámbito en toda la app."""
    response = FileResponse(
        (settings.BASE_DIR / "static" / "service-worker.js").open("rb"),
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response
