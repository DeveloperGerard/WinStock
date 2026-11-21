# PWA de WinStock

## Qué puede hacer actualmente

- Presenta un manifest con el nombre, iconos, colores y modo `standalone` de WinStock.
- Enlaza el manifest y registra un Service Worker desde `/service-worker.js` tanto en `base.html` como en la pantalla de acceso.
- La instalación se inicia desde las opciones habituales del navegador; WinStock no muestra un botón ni intercepta el evento `beforeinstallprompt`.
- Precarga recursos estáticos y guarda una lista blanca de páginas de consulta con estrategia red primero y caché como respaldo.
- Sin conexión, permite consultar las últimas instantáneas de `/`, `/alimentos/`, `/alimentos/stock/`, `/cuentas/`, `/insumos/`, `/ganado/lotes/`, `/raciones/` y `/reportes/`.
- Las instantáneas son de solo lectura: no incluyen formularios, filtros ni acciones de escritura; tampoco guardan tokens CSRF. Crear/editar/eliminar, registrar raciones, filtrar y exportar informes requieren conexión. Las demás rutas muestran `offline.html` cuando no hay red.
- La pantalla base muestra un aviso de modo sin conexión, ofrece revisar la conexión y bloquea las acciones marcadas como solo online. Al recuperar la red, una instantánea abierta se recarga para restaurar los controles.
- Las vistas de cuentas y reportes incluyen datos de funcionarios; al cerrar sesión se borran las instantáneas guardadas del dispositivo.
- Al usar **Cerrar sesión**, la caché de páginas se elimina; la caché de recursos estáticos se conserva.
- Las páginas guardadas son instantáneas y pueden quedar desactualizadas. Al volver la conexión se reactivan los controles; si se estaba viendo la copia de lectura de `/alimentos/`, se actualiza automáticamente para restaurar el formulario online.

## Archivos PWA

```text
ProyectoGit/
├── PWA_README.md
└── winStock/
    ├── templates/
    │   └── base.html
    ├── winstock_project/
    │   ├── urls.py
    │   ├── pwa_views.py
    │   └── settings.py
    ├── static/
    │   ├── manifest.webmanifest
    │   ├── service-worker.js
    │   ├── style.css
    │   └── pwa/
    │       ├── icon-192.png
    │       ├── icon-512.png
    │       └── offline.html
    └── apps/
        └── funcionarios/
            └── templates/
                └── forms/
                    └── inifunc.html
```

### Cómo se conectan

1. `base.html` y `inifunc.html` enlazan `static/manifest.webmanifest` y registran el Service Worker.
2. Desde esas plantillas, Django resuelve la ruta `service_worker` definida en `winstock_project/urls.py`.
3. Esa ruta llama a `pwa_views.py`, que entrega `static/service-worker.js` desde la raíz para darle alcance a toda la aplicación.
4. El Service Worker mantiene cachés versionadas separadas para recursos estáticos y páginas. Guarda las rutas de consulta indicadas arriba solo tras una respuesta correcta y no redirigida. Para guardarlas solicita una variante `offline_snapshot=1`, que elimina controles y tokens CSRF. Si una navegación falla, sirve la instantánea permitida o `offline.html`.
5. `settings.py` define `/static/`, el directorio fuente de estáticos y el destino de `collectstatic`; `style.css` da formato a los controles PWA.
6. La pantalla `apps/funcionarios/templates/forms/inifunc.html` es independiente y **no extiende `base.html`**; por eso tiene sus propios metadatos PWA y registro del Service Worker.

## Instalación según plataforma

- **Windows/Edge o Chrome:** se instala desde la opción que ofrezca el navegador. Si ya está instalada en ese perfil de Edge, puede abrirse desde `edge://apps`; fijarla a Inicio o crear un acceso de escritorio son acciones aparte.
- **Android:** abre el sitio en Chrome y utiliza la opción del navegador para instalar o añadir a la pantalla de inicio.
- **iPhone/iPad:** en Safari, utiliza **Compartir → Añadir a pantalla de inicio**.

Una PWA no es un `.exe` ni un APK. Para que otros dispositivos accedan, el sitio debe estar publicado en un dominio accesible con HTTPS. `localhost` y `127.0.0.1` sirven para pruebas en el mismo dispositivo, no para conectar un teléfono al servidor del computador.

## Prueba local

Desde `winStock/`, inicia Django con `python manage.py runserver` y abre `http://localhost:8000/` o `http://127.0.0.1:8000/`. Inicia sesión y navega por las secciones que tu cuenta tenga permiso para ver mientras hay conexión; WinStock guarda las vistas permitidas para consultarlas después.

En Edge, abre F12 → **Application** → **Service Workers**, espera a que el Service Worker esté activo y marca **Offline**. Recarga las rutas permitidas para consultar sus copias; las demás deben mostrar la pantalla offline. Comprueba que las acciones (por ejemplo, crear insumos, registrar raciones o exportar informes) no se puedan ejecutar. Desmarca **Offline** para comprobar que el aviso desaparece y que la vista se actualiza. Finalmente, usa **Cerrar sesión** para borrar las páginas guardadas.

## Producción y caché

- Publica el sitio con HTTPS, define `DEBUG=False` y configura `ALLOWED_HOSTS` con el dominio publicado.
- Ejecuta `python manage.py collectstatic` y configura el servidor/plataforma para servir `STATIC_ROOT` bajo `/static/`.
- Al cambiar la lista de recursos, incrementa la versión correspondiente (`STATIC_CACHE_NAME` o `PAGES_CACHE_NAME`) en `winStock/static/service-worker.js`.
