function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

async function api(url, options = {}) {
  const csrftoken = getCookie('csrftoken');
  const headers = Object.assign({'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest'}, options.headers || {});
  const res = await fetch(url, Object.assign({credentials: 'same-origin', headers}, options));
  if (!res.ok) throw new Error('HTTP ' + res.status);
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res.text();
}

function confirmar(msg) {
  return Swal.fire({title: '¿Seguro?', text: msg, icon: 'warning', showCancelButton: true, confirmButtonText: 'Sí', cancelButtonText: 'No'});
}

// Favoritos en localStorage
const FAV_KEY = 'optica_favoritos';
function getFavoritos() { try { return JSON.parse(localStorage.getItem(FAV_KEY) || '[]'); } catch (e) { return []; } }
function setFavoritos(arr) { localStorage.setItem(FAV_KEY, JSON.stringify(arr)); actualizarBadgeFav(); }
function toggleFavorito(id, nombre) {
  const arr = getFavoritos();
  const i = arr.findIndex(x => (typeof x === 'object' ? x.id : x) === id);
  if (i >= 0) arr.splice(i, 1); else arr.push({id: id, nombre: nombre || ('Modelo ' + id)});
  setFavoritos(arr);
  return arr.some(x => (typeof x === 'object' ? x.id : x) === id);
}
function favNombres() { return getFavoritos().map(x => typeof x === 'object' ? x.nombre : ('Modelo ' + x)); }
function actualizarBadgeFav() {
  const el = document.querySelector('#fav-count');
  if (el) el.textContent = getFavoritos().length;
}
const COMP_KEY = 'optica_comparar';
function getComparar() { try { return JSON.parse(localStorage.getItem(COMP_KEY) || '[]'); } catch (e) { return []; } }
function setComparar(arr) { localStorage.setItem(COMP_KEY, JSON.stringify(arr.slice(0,3))); actualizarCompareBtn(); }
function toggleComparar(id) {
  const arr = getComparar();
  const i = arr.indexOf(id);
  if (i >= 0) arr.splice(i,1); else if (arr.length < 3) arr.push(id);
  setComparar(arr);
}
function actualizarCompareBtn() {
  const btn = document.querySelector('#compare-btn');
  if (btn) { btn.textContent = 'Comparar (' + getComparar().length + ')'; btn.href = '/comparar/?ids=' + getComparar().join('&ids='); }
}
document.addEventListener('DOMContentLoaded', actualizarBadgeFav);
document.addEventListener('DOMContentLoaded', actualizarCompareBtn);
function toggleDark() {
  document.body.classList.toggle('dark-mode');
  localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}
if (localStorage.getItem('darkMode') === 'true') document.body.classList.add('dark-mode');
if (localStorage.getItem('hc') === 'true') document.body.classList.add('alto-contraste');
if (localStorage.getItem('tg') === 'true') document.body.classList.add('texto-grande');

function aceptarCookies(acepta) {
  localStorage.setItem('cookiesConsent', acepta ? 'accepted' : 'rejected');
  const b = document.getElementById('cookie-banner');
  if (b) b.style.display = 'none';
}
document.addEventListener('DOMContentLoaded', () => {
  const c = localStorage.getItem('cookiesConsent');
  const b = document.getElementById('cookie-banner');
  if (b && !c) b.style.display = 'block';
});

function startTour() {
  const path = window.location.pathname;
  let steps = [{intro: 'Bienvenido/a. Pulsa "Siguiente" para recorrer la aplicación. Puedes pulsar "Saltar" en cualquier momento.'}];
  if (path === '/') {
    steps = steps.concat([
      {element: '.navbar', intro: 'Barra de navegación: catálogo, marcas, citas, contacto.'},
      {element: '.hero', intro: 'Portada con modelos destacados y novedades.'},
      {element: '.floating-wa', intro: 'Botón de WhatsApp para contactar.'},
    ]);
  } else if (path.startsWith('/catalogo')) {
    steps = steps.concat([
      {element: '#filtros', intro: 'Filtra por marca, categoría, género, forma y color. Se actualiza solo.'},
      {element: '#catalogo-grid', intro: 'Resultados: pulsa una gafa para ver detalles o ❤ para favoritos.'},
      {element: '#compare-btn', intro: 'Comparador de hasta 3 modelos.'},
    ]);
  } else if (path.startsWith('/gestion')) {
    steps = steps.concat([
      {element: '.container', intro: 'Panel de gestión: modelos, consultas, citas, ajustes.'},
    ]);
  }
  introJs().setOptions({steps: steps, showStepNumbers: true, exitOnOverlayClick: true}).start();
}

function urlB64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
  return outputArray;
}
async function activarAvisos() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    Swal.fire('No soportado', 'Tu navegador no soporta avisos push', 'info'); return;
  }
  const reg = await navigator.serviceWorker.ready;
  const r = await fetch('/api/push/clave/'); const j = await r.json();
  if (!j.publicKey) { Swal.fire('Sin configurar', 'Faltan claves VAPID', 'warning'); return; }
  const perm = await Notification.requestPermission();
  if (perm !== 'granted') { Swal.fire('Permiso denegado', '', 'warning'); return; }
  let sub = await reg.pushManager.getSubscription();
  if (!sub) {
    sub = await reg.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: urlB64ToUint8Array(j.publicKey)});
    const rs = await fetch('/api/push/suscribir/', {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':getCookie('csrftoken')}, body:JSON.stringify(sub)});
    if (!rs.ok) { Swal.fire('No se pudo activar', 'Inicia sesión en Gestión para recibir avisos', 'warning'); return; }
    Swal.fire('Activado', 'Recibirás un aviso cuando entre una cita o consulta nueva', 'success');
  } else {
    const rp = await fetch('/api/push/probar/', {method:'POST', headers:{'X-CSRFToken':getCookie('csrftoken')}});
    const jp = await rp.json().catch(() => ({}));
    if (jp.enviados > 0) Swal.fire('Ya activado', 'Te hemos enviado un aviso de prueba', 'success');
    else Swal.fire('Aviso no enviado', 'El navegador está suscrito pero el envío falló. Revisa las claves VAPID o vuelve a activarlo.', 'warning');
  }
}

// Enviar selección por WhatsApp
function enviarSeleccionWhatsapp(numero) {
  const ids = getFavoritos();
  if (!ids.length) { Swal.fire('Sin selección', 'Guarda algún modelo primero', 'info'); return; }
  // resolver nombres desde DOM data attributes
  const nombres = favNombres();
  const texto = 'Hola, me interesan estos modelos: ' + nombres.join(', ');
  const url = 'https://wa.me/' + numero + '?text=' + encodeURIComponent(texto);
  window.open(url, '_blank');
}
