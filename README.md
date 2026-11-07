# Óptica Espartinas – Web escaparate

Proyecto Django multi-tenant (core reutilizable) con escaparate público y zona de gestión para la óptica.

## Arranque rápido

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py crear_optica "Óptica Espartinas" laura --password "Laura12345!"
python manage.py collectstatic --noinput
python seed.py
python manage.py runserver 0.0.0.0:8000
```

- Panel admin: http://localhost:8000/admin/
- Gestión: http://localhost:8000/gestion/ (usuario laura)
- Web pública: http://localhost:8000/

## Tests

```bash
python manage.py test
```

## Variables de entorno

Ver `.env.example`. `DJANGO_DEBUG=1` activa live reload.
