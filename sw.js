/* Forma service worker: uygulamayı önbelleğe alır, internet yokken de açılmasını sağlar.
   Yeni sürüm yayınlarken SURUM'ü bir artır; eski önbellek etkinleşme sırasında silinir.
   Kullanıcı verisine (localStorage, IndexedDB) dokunmaz, yalnızca kendi "forma-" önbelleklerini yönetir. */
const SURUM = 'v8';
const CACHE = 'forma-' + SURUM;
const DOSYALAR = ['index.html', 'manifest.webmanifest',
  'icons/apple-touch-icon.png', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-maskable-512.png'];
const AG_BEKLEME = 3000; // sayfa açılırken ağı bu kadar bekle, sonra önbellekten aç
// Hareket görselleri (ex/): kurulumdan sonra arka planda önbelleğe alınır; internetsiz de görünür.
const EX_RESIMLER = ["ex/Ab_Crunch_Machine/0.jpg", "ex/Ab_Crunch_Machine/1.jpg", "ex/Ab_Roller/0.jpg", "ex/Ab_Roller/1.jpg", "ex/Air_Bike/0.jpg", "ex/Air_Bike/1.jpg", "ex/Alternating_Kettlebell_Row/0.jpg", "ex/Alternating_Kettlebell_Row/1.jpg", "ex/Arnold_Dumbbell_Press/0.jpg", "ex/Arnold_Dumbbell_Press/1.jpg", "ex/Back_Flyes_-_With_Bands/0.jpg", "ex/Back_Flyes_-_With_Bands/1.jpg", "ex/Band_Assisted_Pull-Up/0.jpg", "ex/Band_Assisted_Pull-Up/1.jpg", "ex/Band_Good_Morning/0.jpg", "ex/Band_Good_Morning/1.jpg", "ex/Band_Hip_Adductions/0.jpg", "ex/Band_Hip_Adductions/1.jpg", "ex/Band_Pull_Apart/0.jpg", "ex/Band_Pull_Apart/1.jpg", "ex/Band_Skull_Crusher/0.jpg", "ex/Band_Skull_Crusher/1.jpg", "ex/Barbell_Bench_Press_-_Medium_Grip/0.jpg", "ex/Barbell_Bench_Press_-_Medium_Grip/1.jpg", "ex/Barbell_Curl/0.jpg", "ex/Barbell_Curl/1.jpg", "ex/Barbell_Deadlift/0.jpg", "ex/Barbell_Deadlift/1.jpg", "ex/Barbell_Hip_Thrust/0.jpg", "ex/Barbell_Hip_Thrust/1.jpg", "ex/Barbell_Incline_Bench_Press_-_Medium_Grip/0.jpg", "ex/Barbell_Incline_Bench_Press_-_Medium_Grip/1.jpg", "ex/Barbell_Lunge/0.jpg", "ex/Barbell_Lunge/1.jpg", "ex/Bench_Dips/0.jpg", "ex/Bench_Dips/1.jpg", "ex/Bench_Press_-_With_Bands/0.jpg", "ex/Bench_Press_-_With_Bands/1.jpg", "ex/Bent_Over_Barbell_Row/0.jpg", "ex/Bent_Over_Barbell_Row/1.jpg", "ex/Bodyweight_Squat/0.jpg", "ex/Bodyweight_Squat/1.jpg", "ex/Bodyweight_Walking_Lunge/0.jpg", "ex/Bodyweight_Walking_Lunge/1.jpg", "ex/Butt_Lift_Bridge/0.jpg", "ex/Butt_Lift_Bridge/1.jpg", "ex/Cable_Chest_Press/0.jpg", "ex/Cable_Chest_Press/1.jpg", "ex/Cable_Crossover/0.jpg", "ex/Cable_Crossover/1.jpg", "ex/Cable_Crunch/0.jpg", "ex/Cable_Crunch/1.jpg", "ex/Cable_Hip_Adduction/0.jpg", "ex/Cable_Hip_Adduction/1.jpg", "ex/Cable_Rope_Overhead_Triceps_Extension/0.jpg", "ex/Cable_Rope_Overhead_Triceps_Extension/1.jpg", "ex/Calf_Raises_-_With_Bands/0.jpg", "ex/Calf_Raises_-_With_Bands/1.jpg", "ex/Chin-Up/0.jpg", "ex/Chin-Up/1.jpg", "ex/Close-Grip_Barbell_Bench_Press/0.jpg", "ex/Close-Grip_Barbell_Bench_Press/1.jpg", "ex/Close-Grip_Front_Lat_Pulldown/0.jpg", "ex/Close-Grip_Front_Lat_Pulldown/1.jpg", "ex/Concentration_Curls/0.jpg", "ex/Concentration_Curls/1.jpg", "ex/Cross_Over_-_With_Bands/0.jpg", "ex/Cross_Over_-_With_Bands/1.jpg", "ex/Crunches/0.jpg", "ex/Crunches/1.jpg", "ex/Dead_Bug/0.jpg", "ex/Dead_Bug/1.jpg", "ex/Decline_Push-Up/0.jpg", "ex/Decline_Push-Up/1.jpg", "ex/Dip_Machine/0.jpg", "ex/Dip_Machine/1.jpg", "ex/Dips_-_Chest_Version/0.jpg", "ex/Dips_-_Chest_Version/1.jpg", "ex/Dips_-_Triceps_Version/0.jpg", "ex/Dips_-_Triceps_Version/1.jpg", "ex/Dumbbell_Bench_Press/0.jpg", "ex/Dumbbell_Bench_Press/1.jpg", "ex/Dumbbell_Flyes/0.jpg", "ex/Dumbbell_Flyes/1.jpg", "ex/Dumbbell_Shrug/0.jpg", "ex/Dumbbell_Shrug/1.jpg", "ex/Dumbbell_Step_Ups/0.jpg", "ex/Dumbbell_Step_Ups/1.jpg", "ex/EZ-Bar_Skullcrusher/0.jpg", "ex/EZ-Bar_Skullcrusher/1.jpg", "ex/Face_Pull/0.jpg", "ex/Face_Pull/1.jpg", "ex/Farmers_Walk/0.jpg", "ex/Farmers_Walk/1.jpg", "ex/Flat_Bench_Lying_Leg_Raise/0.jpg", "ex/Flat_Bench_Lying_Leg_Raise/1.jpg", "ex/Front_Barbell_Squat/0.jpg", "ex/Front_Barbell_Squat/1.jpg", "ex/Goblet_Squat/0.jpg", "ex/Goblet_Squat/1.jpg", "ex/Hack_Squat/0.jpg", "ex/Hack_Squat/1.jpg", "ex/Hanging_Leg_Raise/0.jpg", "ex/Hanging_Leg_Raise/1.jpg", "ex/Hip_Lift_with_Band/0.jpg", "ex/Hip_Lift_with_Band/1.jpg", "ex/Incline_Dumbbell_Curl/0.jpg", "ex/Incline_Dumbbell_Curl/1.jpg", "ex/Incline_Dumbbell_Press/0.jpg", "ex/Incline_Dumbbell_Press/1.jpg", "ex/Incline_Push-Up/0.jpg", "ex/Incline_Push-Up/1.jpg", "ex/Inverted_Row/0.jpg", "ex/Inverted_Row/1.jpg", "ex/Kettlebell_One-Legged_Deadlift/0.jpg", "ex/Kettlebell_One-Legged_Deadlift/1.jpg", "ex/Kettlebell_Seated_Press/0.jpg", "ex/Kettlebell_Seated_Press/1.jpg", "ex/Lateral_Raise_-_With_Bands/0.jpg", "ex/Lateral_Raise_-_With_Bands/1.jpg", "ex/Leverage_High_Row/0.jpg", "ex/Leverage_High_Row/1.jpg", "ex/Leverage_Shrug/0.jpg", "ex/Leverage_Shrug/1.jpg", "ex/Lying_Leg_Curls/0.jpg", "ex/Lying_Leg_Curls/1.jpg", "ex/Machine_Bench_Press/0.jpg", "ex/Machine_Bench_Press/1.jpg", "ex/Machine_Bicep_Curl/0.jpg", "ex/Machine_Bicep_Curl/1.jpg", "ex/Machine_Triceps_Extension/0.jpg", "ex/Machine_Triceps_Extension/1.jpg", "ex/Monster_Walk/0.jpg", "ex/Monster_Walk/1.jpg", "ex/Natural_Glute_Ham_Raise/0.jpg", "ex/Natural_Glute_Ham_Raise/1.jpg", "ex/One-Arm_Dumbbell_Row/0.jpg", "ex/One-Arm_Dumbbell_Row/1.jpg", "ex/One-Arm_Kettlebell_Swings/0.jpg", "ex/One-Arm_Kettlebell_Swings/1.jpg", "ex/One-Legged_Cable_Kickback/0.jpg", "ex/One-Legged_Cable_Kickback/1.jpg", "ex/Pallof_Press/0.jpg", "ex/Pallof_Press/1.jpg", "ex/Plank/0.jpg", "ex/Plank/1.jpg", "ex/Preacher_Curl/0.jpg", "ex/Preacher_Curl/1.jpg", "ex/Pull_Through/0.jpg", "ex/Pull_Through/1.jpg", "ex/Pullups/0.jpg", "ex/Pullups/1.jpg", "ex/Push-Ups_-_Close_Triceps_Position/0.jpg", "ex/Push-Ups_-_Close_Triceps_Position/1.jpg", "ex/Pushups/0.jpg", "ex/Pushups/1.jpg", "ex/Reverse_Crunch/0.jpg", "ex/Reverse_Crunch/1.jpg", "ex/Romanian_Deadlift/0.jpg", "ex/Romanian_Deadlift/1.jpg", "ex/Russian_Twist/0.jpg", "ex/Russian_Twist/1.jpg", "ex/Seated_Bent-Over_Rear_Delt_Raise/0.jpg", "ex/Seated_Bent-Over_Rear_Delt_Raise/1.jpg", "ex/Seated_Calf_Raise/0.jpg", "ex/Seated_Calf_Raise/1.jpg", "ex/Seated_Dumbbell_Press/0.jpg", "ex/Seated_Dumbbell_Press/1.jpg", "ex/Shoulder_Press_-_With_Bands/0.jpg", "ex/Shoulder_Press_-_With_Bands/1.jpg", "ex/Single-Leg_Leg_Extension/0.jpg", "ex/Single-Leg_Leg_Extension/1.jpg", "ex/Single_Leg_Glute_Bridge/0.jpg", "ex/Single_Leg_Glute_Bridge/1.jpg", "ex/Smith_Machine_Calf_Raise/0.jpg", "ex/Smith_Machine_Calf_Raise/1.jpg", "ex/Smith_Machine_Incline_Bench_Press/0.jpg", "ex/Smith_Machine_Incline_Bench_Press/1.jpg", "ex/Smith_Machine_Overhead_Shoulder_Press/0.jpg", "ex/Smith_Machine_Overhead_Shoulder_Press/1.jpg", "ex/Smith_Machine_Squat/0.jpg", "ex/Smith_Machine_Squat/1.jpg", "ex/Smith_Single-Leg_Split_Squat/0.jpg", "ex/Smith_Single-Leg_Split_Squat/1.jpg", "ex/Split_Squat_with_Dumbbells/0.jpg", "ex/Split_Squat_with_Dumbbells/1.jpg", "ex/Squats_-_With_Bands/0.jpg", "ex/Squats_-_With_Bands/1.jpg", "ex/Standing_Biceps_Cable_Curl/0.jpg", "ex/Standing_Biceps_Cable_Curl/1.jpg", "ex/Standing_Dumbbell_Calf_Raise/0.jpg", "ex/Standing_Dumbbell_Calf_Raise/1.jpg", "ex/Standing_Dumbbell_Triceps_Extension/0.jpg", "ex/Standing_Dumbbell_Triceps_Extension/1.jpg", "ex/Standing_Leg_Curl/0.jpg", "ex/Standing_Leg_Curl/1.jpg", "ex/Standing_Military_Press/0.jpg", "ex/Standing_Military_Press/1.jpg", "ex/Stiff-Legged_Dumbbell_Deadlift/0.jpg", "ex/Stiff-Legged_Dumbbell_Deadlift/1.jpg", "ex/Straight-Arm_Pulldown/0.jpg", "ex/Straight-Arm_Pulldown/1.jpg", "ex/Superman/0.jpg", "ex/Superman/1.jpg", "ex/T-Bar_Row_with_Handle/0.jpg", "ex/T-Bar_Row_with_Handle/1.jpg", "ex/Trap_Bar_Deadlift/0.jpg", "ex/Trap_Bar_Deadlift/1.jpg", "ex/Tricep_Dumbbell_Kickback/0.jpg", "ex/Tricep_Dumbbell_Kickback/1.jpg"];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE)
    .then(c => c.addAll(DOSYALAR.map(u => new Request(u, { cache: 'reload' }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k.startsWith('forma-') && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim())
    .then(() => { gorselleriDoldur(); }));
});

// Eksik hareket görsellerini sırayla indir; biri başarısız olursa diğerleri devam eder.
async function gorselleriDoldur(){
  const c = await caches.open(CACHE);
  for (const u of EX_RESIMLER){
    try { if (!(await c.match(u))) { const r = await fetch(u); if (r.ok) await c.put(u, r); } } catch (err) {}
  }
}

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

  // Hareket görselleri: önbellekte varsa oradan, yoksa ağdan alıp önbelleğe koy.
  if (url.pathname.includes('/ex/')) {
    e.respondWith(caches.match(req, { ignoreSearch: true }).then(r => r || fetch(req).then(res => {
      if (res.ok) { const kopya = res.clone(); caches.open(CACHE).then(c => c.put(req, kopya)); }
      return res;
    })));
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
