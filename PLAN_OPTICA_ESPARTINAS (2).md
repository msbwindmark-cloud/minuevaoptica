# Plan – Web escaparate para Óptica Espartinas ("The Best of the Best")

Basado en `ESPECIFICACIONES.md` (Django multi-tenant, WhiteNoise, live reload solo en debug, auditoría, PWA mobile-first).

**Meta:** que sea la web de óptica más cuidada de su zona: rapidísima, preciosa en el móvil, con experiencias que nadie más tiene (probador virtual, buscador de montura por tipo de cara, códigos QR en el escaparate) y conectada con la tienda física.

---

## 1. Idea en una frase
Una web **escaparate** (no tienda online): la gente ve los modelos, el diseño y la información de la óptica, y **contacta** (WhatsApp, teléfono, formulario o cita). Nadie compra ni paga en la web.

## 2. Tema legal (importante)
- En España la venta online de gafas graduadas y lentillas está muy restringida por sanidad. **Por eso: sin carrito, sin pago, sin "comprar".**
- Mostrar un catálogo con fotos y descripciones es publicidad/escaparate. Los botones serán del tipo **"Consultar disponibilidad"**, **"Pedir cita"** o **"Escribir por WhatsApp"**.
- Evita precios cerrados de gafas graduadas; mejor "desde X €" o "consultar en tienda" (ella decide).
- Confirma con tu amiga (o con el Colegio de Ópticos-Optometristas de Andalucía) qué puede publicar en cuanto a publicidad sanitaria. No prometas nada médico ("cura", "mejora la vista") en los textos.
- Obligatorio en la web (LSSI + RGPD): **Aviso legal, Política de privacidad, Política de cookies** y casilla de consentimiento en el formulario de contacto. Ella es la responsable del tratamiento de los datos; tú, el encargado (firmad un contrato sencillo de encargado de tratamiento).
- Cualquier función con cámara (probador virtual) se procesa **solo en el móvil del visitante**: no se sube ni se guarda ninguna foto. Hay que decirlo claramente en la política de privacidad.

## 3. Tipos de usuario

| Quién | Accede a | Cómo |
|---|---|---|
| **Visitante** (público) | Solo ver: inicio, catálogo, detalle de modelo, contacto, info | Sin login. No puede crear, editar ni borrar nada. Solo puede **enviar** el formulario de contacto o de cita |
| **Gestora** (tu amiga) | Zona privada `/gestion/`: artículos, fotos, descripciones, mensajes recibidos | Login propio. Rol `gestor` |
| **Tú (superusuario)** | Panel `/admin/` completo: modelos, usuarios, auditoría, ajustes | Login superusuario |

- Los visitantes **no tienen cuenta** ni ninguna URL que escriba datos, salvo el formulario de contacto/cita (con CSRF, límite de envíos y campo trampa anti-spam).
- La gestora **no entra en `/admin/`**: tiene su propia zona sencilla, hecha con vistas Django y plantillas (mobile-first, botones grandes, confirmación al borrar con SweetAlert2). Así no puede romper nada ni ver cosas técnicas.
- Tú ves todo en el admin, incluida la auditoría.

## 4. Acceso de la gestora (sin usar el panel admin)

### 4.1 Alta (una sola vez, la haces tú)
- Desde tu panel admin, o con un comando de gestión (`python manage.py crear_optica "Óptica Espartinas" laura --password "..."`), se crea:
  - un `User` normal **sin** `is_staff` ni `is_superuser` (así `/admin/` le queda cerrado), y
  - un `Perfil` con la organización de la óptica y `rol = gestor`.

### 4.2 Cómo entra ella
- URL propia: `opticaespartinas.es/gestion/` (login en `/gestion/login/`), con el diseño de la web y el botón "ojo" para ver la contraseña.
- Si no hay sesión, Django la redirige al login; tras entrar va a su panel `/gestion/`.
- Enlace discreto **"Acceso gestión"** en el pie de la web.
- Puede **instalar la web como app** en el móvil (PWA) con un manifest específico `start_url=/gestion/`, de modo que el icono de su pantalla de inicio abra directamente su panel.

### 4.3 Protección
- `LOGIN_URL = "/gestion/login/"` y `LOGIN_REDIRECT_URL = "/gestion/"`.
- Todas las vistas de `/gestion/` llevan `@login_required` y `@gestor_required` (comprueba rol y organización). Sin login → login; otro rol → 403.
- Límite de intentos de login fallidos (bloqueo temporal por IP/usuario) y cada intento queda en la auditoría.
- Sesión que dura lo razonable en el móvil (por ejemplo 30 días con "recordarme"), pero cierra sola en ordenadores compartidos si no marca la casilla.

### 4.4 Contraseña olvidada
- Opción A: la restableces tú desde el admin.
- Opción B (recomendada): "¿Has olvidado tu contraseña?" con el sistema de Django y envío de enlace por email (ya configurado en el `.env`).

## 5. Estructura del proyecto
```
core/        # Organizacion, Perfil (rol), TenantModel, Auditoria, middleware (reutilizado)
optica/      # modelos y vistas del escaparate
templates/   # base.html, publico/, gestion/
static/      # css, js, iconos PWA, sw.js, modelos de IA del probador
media/       # fotos de las gafas
```
Aunque ahora es una sola óptica, se mantiene `Organizacion` para reutilizar `core` y poder ofrecer lo mismo a otra óptica sin rehacer nada.

## 6. Modelos (app `optica`)
Todos heredan de `TenantModel` y se auditan.

- **Ajustes** (uno por organización): nombre comercial, dirección, teléfono, WhatsApp, email, horario (con festivos/vacaciones), enlace Google Maps, redes, texto de portada, logo, colores de marca.
- **Marca**: nombre, logo, orden, visible.
- **Categoria**: nombre y slug (Gafas de sol, Monturas graduadas, Infantil, Deportivas, Accesorios).
- **Modelo** (la gafa): marca, categoría, nombre/referencia, slug, descripción corta y larga, precio opcional (o "consultar"), material, forma (redonda, cuadrada, aviador, cat-eye…), tamaño (ancho de lente/puente/varilla), color, género, `destacado`, `novedad`, `visible`, fecha de alta, orden.
- **FotoModelo**: modelo (FK), imagen, texto alternativo, orden. La primera es la portada.
- **Variante/Color** (opcional): un mismo modelo en varios colores, cada uno con sus fotos.
- **Consulta**: nombre, teléfono, email, mensaje, modelo (opcional), fecha, `leida`, consentimiento RGPD (bool + fecha).
- **Cita**: nombre, teléfono, fecha/hora deseada, motivo (revisión, adaptación, reparación, lentillas), estado (pendiente, confirmada, cancelada).
- **Entrada** (blog/novedades): título, texto, imagen, publicada.
- **Opinion** (opcional): textos de clientes que ella elige mostrar, con permiso.
- **Auditoria** (de `core`): todo lo que hace la gestora y tú.

Las fotos se redimensionan al subirlas (máx. 1600 px, WebP/JPEG comprimido, con miniaturas) para que la web vuele en el móvil y no se llene el hosting.

## 7. Páginas públicas
- `/` Portada: banner, modelos destacados y novedades, horario, estado "Abierto ahora / Cerrado" calculado, botón WhatsApp.
- `/catalogo/` Listado con filtros (marca, categoría, género, forma, color), búsqueda y paginación.
- `/catalogo/<slug>/` Detalle: galería, descripción, medidas, botones "Consultar por WhatsApp" (con el nombre del modelo ya escrito), "Pedir cita", "Probar en mi cara" y "Guardar en favoritos".
- `/marcas/` y `/marcas/<slug>/`
- `/encuentra-tu-montura/` Cuestionario por tipo de cara (sección 8).
- `/favoritos/` y `/comparar/` (sección 8).
- `/citas/` Solicitud de cita.
- `/novedades/` Blog/lookbook.
- `/contacto/` Formulario + mapa + horario + teléfono.
- `/nosotros/` Quiénes somos, servicios (revisión de vista, adaptación, reparaciones, ajustes).
- `/aviso-legal/`, `/privacidad/`, `/cookies/`

## 8. Funciones "wow" (lo que nadie más tendrá)

1. **Probador virtual con la cámara** ("Pruébatelas"): el visitante abre la cámara del móvil y ve las gafas sobre su cara en tiempo real. Se hace en el navegador (MediaPipe Face Landmarker + Three.js o PNG transparente anclado a los ojos), sin enviar nada al servidor. Cada modelo necesita una foto frontal con fondo transparente; la gestora la sube al dar de alta la gafa. Si el móvil no soporta cámara, el botón no aparece.
2. **Encuentra tu montura**: cuestionario de 4-5 preguntas (forma de la cara, estilo, uso, color) que recomienda modelos del catálogo, con resultado compartible por WhatsApp.
3. **Favoritos y "mi selección"**: el visitante guarda modelos (en el navegador, sin crear cuenta) y con un botón envía **su lista completa a la óptica por WhatsApp** o pide cita para probárselos. Conecta la web con la tienda.
4. **Comparador** de 2-3 modelos lado a lado (medidas, material, forma).
5. **Visor 360° / zoom** en las fotos de cada gafa con gestos táctiles.
6. **Códigos QR en el escaparate y en las monturas**: cada modelo tiene su QR (la app lo genera e imprime en PDF). Escaneas en la tienda o en la calle y abres su ficha. Puente directo entre lo físico y lo digital.
7. **Modo noche/día** y diseño con animaciones suaves (scroll, transiciones de las galerías), tipografía elegante y paleta propia de la óptica.
8. **Estado de la tienda en tiempo real**: "Abierto hasta las 20:00" / "Abrimos mañana a las 10:00", y banner para vacaciones o festivos.
9. **Recordatorio de revisión** (opcional, con consentimiento): la clienta deja su email/teléfono y recibe un aviso anual para revisar la vista. La gestora ve la lista.
10. **Reseñas de Google integradas** y enlace para "Déjanos tu opinión" con QR en el mostrador.
11. **Avisos push a la gestora** (Web Push, ya definido en las especificaciones): le suena el móvil cuando llega una consulta o una cita nueva.
12. **Multi-idioma** (es/en) si hay turismo o clientes extranjeros.
13. **Accesibilidad de verdad** (muy coherente en una óptica): alto contraste, tamaño de letra ajustable, navegación por teclado, textos alternativos y cumplimiento WCAG AA.
14. **Funciona sin conexión** (PWA): el catálogo visitado queda en caché y se abre aunque falle la cobertura.

## 9. Zona de gestión (`/gestion/`)
- **Panel**: modelos totales, consultas y citas sin leer, últimos cambios, modelos más vistos y más guardados en favoritos.
- **Modelos**: listar (búsqueda AJAX en tiempo real, paginación), crear, editar, ocultar/mostrar con un interruptor, marcar destacado/novedad, subir y reordenar fotos arrastrando (cámara móvil con `capture`), subir la imagen transparente para el probador, borrar con confirmación.
- **Importación masiva** desde Excel/CSV (útil para cargar el catálogo inicial) y **exportación**.
- **Marcas y categorías**: CRUD simple.
- **Consultas y citas**: bandeja con "marcar como leída", confirmar/cancelar cita, botón de responder por WhatsApp o email con plantilla.
- **Generador de QR** por modelo (descarga PDF para imprimir etiquetas).
- **Novedades/blog**: publicar entradas con foto.
- **Ajustes de la óptica**: horario, vacaciones, teléfonos, textos de portada.
- **Mi historial**: lista de sus últimas acciones (viene de la auditoría).
- Permisos: decoradores `@gestor_required`; todas las vistas filtran por `request.organizacion`.

## 10. Seguridad del lado público
- Solo vistas `GET` públicas y solo ven `visible=True`.
- Formularios: CSRF, *honeypot*, límite de envíos por IP (por ejemplo 5 por hora con caché), validación de teléfono/email, sin HTML permitido.
- Subida de fotos solo desde la zona privada, validando tipo, tamaño y contenido real de la imagen.
- `DEBUG=0`, `SECRET_KEY` en `.env`, HTTPS, cabeceras de seguridad de Django y `Content-Security-Policy` razonable.
- Los visitantes nunca ven datos de consultas, usuarios ni auditoría.

## 11. Rendimiento y SEO (parte de "the best")
- Objetivo: Lighthouse 90+ en móvil. Imágenes WebP con `srcset` y `loading="lazy"`, CSS/JS mínimos, WhiteNoise con compresión y caché de larga duración.
- SEO local: títulos y meta descriptions por modelo, `sitemap.xml`, `robots.txt`, datos estructurados `LocalBusiness` y `Product` (sin precio si no se muestra), URLs limpias con slug.
- Alta y cuidado de **Google Business Profile** (fotos, horario, reseñas): es lo que más clientes trae en una óptica local.
- Previsualizaciones bonitas al compartir (Open Graph/Twitter Cards) con la foto del modelo.
- Analítica respetuosa sin cookies (Plausible/Umami) para no necesitar banner pesado.

## 12. Requisitos heredados de las especificaciones
- **WhiteNoise** para estáticos y `collectstatic` antes de desplegar.
- **Live reload** (`django-browser-reload`) solo con `DJANGO_DEBUG=1`.
- **Auditoría** de altas, ediciones, borrados, logins, subidas de fotos, envío de avisos y exportaciones.
- **Mobile-first y PWA** (manifest + service worker): la gestora instala la app y sube gafas directamente con la cámara.
- Variables en `.env`; SQLite en desarrollo, PostgreSQL/MySQL en producción si hace falta.

## 13. Fases

1. **MVP (para enseñárselo)**: modelos, portada, catálogo, detalle, contacto con WhatsApp, páginas legales, admin para ti, `seed.py`.
2. **Zona de gestión**: login propio, CRUD de modelos con fotos, bandeja de consultas, ajustes.
3. **Pulido y rendimiento**: diseño final, SEO, redimensionado de imágenes, Maps, filtros, estado "abierto ahora".
4. **Wow nivel 1**: favoritos + enviar selección por WhatsApp, comparador, QR por modelo, citas, push a la gestora.
5. **Wow nivel 2**: probador virtual con cámara, "Encuentra tu montura", visor 360°, recordatorios de revisión, blog.
6. **Extras**: multi-idioma, reseñas de Google integradas, estadísticas.

## 14. Despliegue barato
- **PythonAnywhere** (como el taller) o un VPS pequeño. Dominio tipo `opticaespartinas.es` (unos 10 €/año) apuntando al hosting.
- Cuidado con el espacio de `media/`: se comprimen las fotos y se generan miniaturas.
- Copias de seguridad: `dumpdata` + copia de `media/` programada.
- El probador virtual es todo cliente (JS), así que no consume recursos del servidor.

## 15. Modelo de negocio sugerido
- Cuota de creación + mantenimiento mensual pequeño (dominio, hosting, cambios).
- Si es un favor entre amigos, deja por escrito qué incluye (cambios, hosting, dominio).
- Al ser multi-tenant, puedes ofrecer lo mismo a otras ópticas y comercios locales: el probador y el QR son tu argumento de venta diferencial.

## 16. Correo (Gmail con app password)

### 16.1 Configuración
- Usa la cuenta Gmail del desarrollador con **contraseña de aplicación** (requiere verificación en dos pasos activada).
- Variables en `.env` (ya definidas en `ESPECIFICACIONES.md`): `EMAIL_HOST=smtp.gmail.com`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=1`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`.
- **La app password solo vive en el `.env`** (en `.gitignore`; en PythonAnywhere, en las variables del entorno de producción). Nunca en el código, en un `.md` ni en un chat. Si se filtra, se revoca desde la cuenta Google y se crea otra.
- En desarrollo: `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` para ver los correos en la terminal sin enviarlos.
- Remitente con el nombre de la óptica: `DEFAULT_FROM_EMAIL="Óptica Espartinas <tucuenta@gmail.com>"`, y el email de la gestora en `reply_to` para que las respuestas le lleguen a ella.
- Límite de Gmail: unos 500 envíos al día en cuentas personales; de sobra para una óptica local.
- Más adelante: migrar a un correo con el dominio (`info@opticaespartinas.es`) con SPF/DKIM/DMARC para evitar spam.

### 16.2 Correos automáticos
| Evento | Destinatario | Contenido |
|---|---|---|
| Nueva consulta | Óptica | Datos, mensaje, modelo consultado, botón de WhatsApp |
| Nueva consulta | Cliente | "Hemos recibido tu mensaje, te respondemos en breve" |
| Solicitud de cita | Óptica y cliente | Fecha pedida, estado "pendiente" |
| Cita confirmada/cancelada | Cliente | Fecha, hora, dirección y mapa, archivo `.ics` para el calendario |
| Recordatorio de cita (24 h antes) | Cliente | Con enlace para cancelar |
| Recuperar contraseña | Gestora | Enlace de Django con caducidad |
| Recordatorio de revisión anual (con consentimiento) | Cliente | Invitación a pedir cita |
| Alta de usuario / cambio de contraseña | Gestora | Aviso de seguridad |

### 16.3 Buenas prácticas
- Plantillas HTML + texto plano, con el logo y los colores de la óptica.
- Envío fuera de la petición (hilo o cola sencilla, por ejemplo un comando programado) para que el formulario no se quede esperando a Gmail; si falla, se reintenta y queda en la auditoría.
- Modelo `EnvioCorreo` (destinatario, asunto, tipo, fecha, estado, error) para saber qué se envió y qué falló.
- Todo correo comercial o recordatorio lleva enlace de baja y solo se envía con consentimiento.

## 17. Más sugerencias para que sea la leche

### 17.1 Marca y contenido (el 50 % de que parezca "premium")
- Define antes de programar: **logo, paleta de 2-3 colores, tipografías (una para títulos y otra para texto) y tono de voz**. Si ella no tiene logo, hazle una propuesta sencilla.
- **Fotos con una guía mínima**: fondo blanco o neutro, luz natural, mismo encuadre en todos los modelos (frontal, lateral, 3/4). Dale una mini guía de una página para que las suba ella con el móvil. Unas buenas fotos valen más que cualquier función.
- Sesión de fotos o vídeo corto de la tienda y del equipo en la página "Nosotros": genera confianza.
- Textos locales y cercanos: Espartinas, Aljarafe, Sevilla.

### 17.2 Integración con la tienda física
- **WhatsApp Business**: crea el catálogo y las respuestas rápidas allí y enlaza la web con el número. El botón de cada modelo abre un mensaje ya escrito.
- **Etiquetas con QR** en monturas y escaparate (el generador ya está en la zona de gestión), y un **QR de reseñas** en el mostrador.
- **Tarjeta de visita o flyer** con el QR de la web.
- **Pantalla o tablet en la tienda** con la web en modo "catálogo" para mostrar modelos que no están expuestos.

### 17.3 Calidad y seguridad como developer
- **Git desde el primer día** (repositorio privado en GitHub, ramas `main` y `desarrollo`, `.gitignore` con `.env`, `db.sqlite3`, `media/`).
- **Tests** para lo crítico: aislamiento entre organizaciones, que el visitante no pueda escribir, permisos de la gestora, que la auditoría registra, que los formularios validan.
- **Sentry** (plan gratuito) para enterarte de los errores en producción antes que ella. Aviso por email.
- **UptimeRobot** (gratuito) para que te avise si la web se cae.
- **Copias de seguridad automáticas** de la base de datos y de `media/`, y probar una vez cómo se restaura.
- **Verificación en dos pasos opcional** para la gestora (y obligatoria para ti como superusuario).
- **`python manage.py check --deploy`** antes de cada despliegue.
- **Entorno de pruebas (staging)** con datos falsos para enseñarle cambios antes de publicarlos.

### 17.4 Experiencia para la gestora (que se enamore del panel)
- **Manual corto** `MANUAL_OPTICA.md` con capturas: subir una gafa, ocultarla, responder una consulta, imprimir un QR. Una página por tarea.
- Asistente "**Añadir gafa en 30 segundos**": foto desde la cámara, marca, nombre, y listo; el resto de campos son opcionales y se completan después.
- **Duplicar modelo** (para colores y variantes) y **acciones en lote** (ocultar varias, cambiar categoría).
- **Estados claros**: borrador, publicada, oculta, agotada ("Consultar disponibilidad").
- **Vista previa** de cómo se verá el modelo en la web antes de publicarlo.
- Panel con lo que importa: consultas sin responder, citas de hoy y de mañana, modelos más vistos.
- Zona de gestión en **modo oscuro** y con botones grandes para usar de pie, con una mano.

### 17.5 Detalles que se notan
- Pantalla de carga elegante, animaciones sutiles y *skeletons* mientras cargan las fotos.
- Páginas 404 y 500 personalizadas con humor y un botón para ir al catálogo.
- Botón flotante de WhatsApp discreto y accesible, que no tape contenido en móvil.
- Etiqueta "Nuevo" y "Últimas unidades" según lo que ella indique (sin presionar al cliente de forma engañosa).
- Mapa con indicaciones y botón "Cómo llegar" que abre Google Maps/Waze.
- Sección de **preguntas frecuentes** (cuándo cambiar de gafas, cómo cuidarlas, qué incluye la revisión), buena para SEO.
- Banner de cookies sencillo y legal, sin trucos.

### 17.6 Crecimiento (cuando la web ya funcione)
- **Google Business Profile** al día: fotos nuevas cada mes, horario, publicaciones y respuesta a reseñas.
- **Campañas de temporada**: gafas de sol en primavera, vuelta al cole con monturas infantiles, Black Friday con avisos a quien dio consentimiento.
- **Newsletter opcional** (con consentimiento y baja) con novedades y recordatorios de revisión.
- **Estadísticas mensuales** en un resumen de una página para ella: visitas, modelos más vistos, consultas recibidas, citas generadas. Demuestra el valor de tu trabajo y justifica la cuota.

### 17.7 Para ti como desarrollador
- Guarda esto como **plantilla reutilizable**: proyecto base con `core`, auditoría, WhiteNoise, PWA y zona de gestión. La próxima óptica, tienda o negocio local se monta en días.
- Documenta cada decisión en `ESPECIFICACIONES.md` según la tomes; es lo que te permite retomar el proyecto en una conversación nueva sin gastar créditos explicando todo otra vez.
- Cuando algo funcione, haz una captura o un vídeo corto: será tu portfolio para conseguir más clientes.

## 18. Prompt para pasar a un asistente al empezar el proyecto
> Crea un proyecto Django siguiendo `ESPECIFICACIONES.md` (core multi-tenant, WhiteNoise, django-browser-reload solo con DEBUG, modelo Auditoria) y `PLAN_OPTICA_ESPARTINAS.md`. Empieza por la fase 1: modelos de `optica`, vistas públicas (portada, catálogo, detalle, contacto, legales), admin para el superusuario y `seed.py` con datos de prueba. Sin carrito ni pagos. Deja preparada la estructura para `/gestion/` con login propio y rol `gestor`.

## 19. Checklist
- [ ] Hablar con la dueña: precios a mostrar, textos, fotos, logo, horario, colores y estilo
- [ ] Definir marca (logo, paleta, tipografías) y guía de fotos
- [ ] Repositorio Git privado, `.gitignore` con `.env`, y app password de Gmail solo en `.env`
- [ ] Correos automáticos (sección 16) probados con backend de consola y luego con Gmail
- [ ] Sentry, UptimeRobot y copias de seguridad configurados
- [ ] `MANUAL_OPTICA.md` para la gestora
- [ ] Confirmar con ella la parte legal (publicidad sanitaria)
- [ ] Crear proyecto con la plantilla de `ESPECIFICACIONES.md`
- [ ] Modelos + admin + seed
- [ ] Páginas públicas + contacto con WhatsApp
- [ ] Páginas legales + banner de cookies
- [ ] Zona `/gestion/` con rol `gestor` y manifest PWA propio
- [ ] Favoritos, comparador, QR y citas
- [ ] Probador virtual y "Encuentra tu montura"
- [ ] Tests: visitante no puede escribir, gestora solo ve lo suyo y no entra en `/admin/`, auditoría registra
- [ ] Lighthouse 90+ en móvil
- [ ] Desplegar con `DEBUG=0`, dominio y HTTPS
- [ ] Alta en Google Business Profile y enviar el sitemap a Google
