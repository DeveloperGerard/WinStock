# PWA de WinStock

## Qué puede hacer actualmente

- Presenta un manifest con el nombre, iconos, colores y modo `standalone` de WinStock.
- Enlaza el manifest y registra un Service Worker desde `/service-worker.js` tanto en `base.html` como en la pantalla de acceso.
- Muestra **Instalar WinStock** solo si el navegador emite `beforeinstallprompt`. La instalación y el acceso resultante los administra el navegador; Edge no fija automáticamente la aplicación al menú Inicio ni al escritorio.
- El botón propio y la ayuda de instalación para iOS solo están en páginas que usan `base.html`; la pantalla de acceso permite que el navegador detecte el manifest, pero no tiene ese botón.
- Precarga recursos estáticos y guarda una lista blanca de páginas de consulta con estrategia red primero y caché como respaldo.
- Sin conexión, permite consultar las últimas respuestas guardadas para `/`, `/alimentos/` y `/alimentos/stock/`. La copia de `/alimentos/` no incluye el formulario de creación ni su token CSRF.
- No guarda pantallas de login, formularios, rutas de edición/deshabilitación ni páginas de insumos, ganado, reportes o cuentas. Si una ruta no permitida no está disponible en línea, muestra `offline.html`.
- La pantalla base avisa cuando no hay conexión y bloquea las acciones marcadas como solo online. La pantalla de acceso deshabilita su formulario porque iniciar sesión requiere conexión.
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

1. `base.html` y `inifunc.html` enlazan `static/manifest.webmanifest` y registran el Service Worker. `base.html` además contiene el botón de instalación, su interacción y la ayuda de iOS.
2. Desde esas plantillas, Django resuelve la ruta `service_worker` definida en `winstock_project/urls.py`.
3. Esa ruta llama a `pwa_views.py`, que entrega `static/service-worker.js` desde la raíz para darle alcance a toda la aplicación.
4. El Service Worker mantiene cachés versionadas separadas para recursos estáticos y páginas. Solo guarda `/`, `/alimentos/` y `/alimentos/stock/`, después de una respuesta correcta que no sea una redirección. Para `/alimentos/`, solicita una variante de lectura que omite el formulario y el token CSRF antes de guardarla. Si una navegación falla, sirve su instantánea permitida o `offline.html`.
5. `settings.py` define `/static/`, el directorio fuente de estáticos y el destino de `collectstatic`; `style.css` da formato a los controles PWA.
6. La pantalla `apps/funcionarios/templates/forms/inifunc.html` es independiente y **no extiende `base.html`**; por eso tiene sus propios metadatos PWA y registro del Service Worker. No contiene el botón propio de instalación.

## Instalación según plataforma

- **Windows/Edge o Chrome:** se instala desde la opción que ofrezca el navegador. Si ya está instalada en ese perfil de Edge, puede abrirse desde `edge://apps`; fijarla a Inicio o crear un acceso de escritorio son acciones aparte.
- **Android:** abre el sitio en Chrome y utiliza la opción de instalar o añadir a la pantalla de inicio. El botón propio, disponible tras iniciar sesión, depende de que Chrome emita `beforeinstallprompt`.
- **iPhone/iPad:** no se usa `beforeinstallprompt`; en Safari se añade desde **Compartir → Añadir a pantalla de inicio**. El texto de ayuda de WinStock solo aparece después de iniciar sesión, en páginas que usan `base.html`.

Una PWA no es un `.exe` ni un APK. Para que otros dispositivos accedan, el sitio debe estar publicado en un dominio accesible con HTTPS. `localhost` y `127.0.0.1` sirven para pruebas en el mismo dispositivo, no para conectar un teléfono al servidor del computador.

## Prueba local

Desde `winStock/`, inicia Django con `python manage.py runserver` y abre `http://localhost:8000/` o `http://127.0.0.1:8000/`. Inicia sesión y visita `/`, `/alimentos/` y `/alimentos/stock/` con conexión para guardar sus instantáneas.

En Edge, abre F12 → **Application** → **Service Workers**, espera a que el Service Worker esté activo y marca **Offline**. Recarga las rutas permitidas para consultar sus copias; las demás deben mostrar la pantalla offline. Para comprobar que agregar, modificar y deshabilitar quedan bloqueados, deja abierta una de esas páginas antes de marcar **Offline**. La pantalla de acceso debe explicar que iniciar sesión requiere Internet y mantener el botón deshabilitado. Desmarca **Offline** para comprobar que el aviso desaparece y que los controles se reactivan; la copia de lectura de `/alimentos/` se actualiza automáticamente. Finalmente, vuelve a conectarte y usa **Cerrar sesión** para borrar las páginas guardadas.

El botón no aparece si el navegador no ofrece `beforeinstallprompt` o si la aplicación ya está instalada. En Edge, revisa `edge://apps` para comprobar si WinStock ya está instalada en el perfil.

## Producción y caché

- Publica el sitio con HTTPS, define `DEBUG=False` y configura `ALLOWED_HOSTS` con el dominio publicado.
- Ejecuta `python manage.py collectstatic` y configura el servidor/plataforma para servir `STATIC_ROOT` bajo `/static/`.
- Al cambiar la lista de recursos, incrementa la versión correspondiente (`STATIC_CACHE_NAME` o `PAGES_CACHE_NAME`) en `winStock/static/service-worker.js`.
