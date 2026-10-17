/* Forma service worker: uygulamayı önbelleğe alır, internet yokken de açılmasını sağlar.
   Yeni sürüm yayınlarken SURUM'ü bir artır; eski önbellek etkinleşme sırasında silinir.
   Kullanıcı verisine (localStorage, IndexedDB) dokunmaz, yalnızca kendi "forma-" önbelleklerini yönetir. */
const SURUM = 'v1';
const CACHE = 'forma-' + SURUM;
const DOSYALAR = ['index.html', 'manifest.webmanifest',
  'icons/apple-touch-icon.png', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-maskable-512.png'];
const AG_BEKLEME = 3000; // sayfa açılırken ağı bu kadar bekle, sonra önbellekten aç

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE)
    .then(c => c.addAll(DOSYALAR.map(u => new Request(u, { cache: 'reload' }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k.startsWith('forma-') && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

const uygulamaSayfasi = url => url.pathname.endsWith('/') || url.pathname.endsWith('/index.html');

self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return; // AI istekleri ve dış adresler olduğu gibi geçer

  // Uygulama sayfası: önce ağ (yeni sürüm hemen gelsin), ağ yoksa ya da yavaşsa önbellek.
  if (req.mode === 'navigate' && uygulamaSayfasi(url)) {
    const ag = fetch(req, { cache: 'no-cache' }).then(res => {
      if (res.ok) { const kopya = res.clone(); caches.open(CACHE).then(c => c.put('index.html', kopya)); }
      return res;
    });
    e.waitUntil(ag.catch(() => {}));
    const yedek = () => caches.match('index.html');
    const bekle = new Promise(r => setTimeout(r, AG_BEKLEME)).then(yedek);
    e.respondWith(Promise.race([ag.catch(yedek), bekle.then(r => r || ag)]).then(r => r || ag));
    return;
  }

  // Diğer dosyalar (ikonlar, manifest): önbellekten ver, arkada tazele.
  if (!DOSYALAR.some(d => url.pathname.endsWith('/' + d))) return;
  e.respondWith(caches.match(req, { ignoreSearch: true }).then(onbellek => {
    const ag = fetch(req).then(res => {
      if (res.ok) { const kopya = res.clone(); caches.open(CACHE).then(c => c.put(req, kopya)); }
      return res;
    });
    if (onbellek) { e.waitUntil(ag.catch(() => {})); return onbellek; }
    return ag;
  }));
});
