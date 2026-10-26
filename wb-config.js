// Config penyimpanan (Cloudflare Worker) - akun alifavif-cmd
// Satu Worker dipakai semua akun; data tiap akun dipisah lewat nama "account".
window.WB_STORE = {
  worker: 'https://steep-resonance-6a71.kjago7822.workers.dev',
  account: 'alifavif-cmd',
  // Link di akhir kopipasta trek (prediksi.html): memakai link scenangka
  siteUrl: 'https://scenangka.github.io/Scenangka/',
  // Daftar link Toko Member (dipakai toko.html alifavif; kunci buka/tutup diatur dari admin scenangka)
  tokoLinks: [
    { id: 'kjago7822',                    url: 'https://kjago7822.github.io/WB-PREDICTION-/' },
    { id: 'wgus543-hub',                  url: 'https://wgus543-hub.github.io/WB-PREDICTION-/' },
    { id: 'mamakeavif-star',              url: 'https://mamakeavif-star.github.io/WB-PREDICTION-/' },
    { id: 'adinealif-byte',               url: 'https://adinealif-byte.github.io/WB-PREDICTION-/' },
    { id: 'paitoangka1234-cpu',           url: 'https://paitoangka1234-cpu.github.io/WB-scen/' },
    { id: 'kpps33040420090144-creator',   url: 'https://kpps33040420090144-creator.github.io/WB-PREDICTION-/' },
    { id: 'bototomart787-png',            url: 'https://bototomart787-png.github.io/Scenangka/' }
  ],
  // Firebase blog (tombol "Kirim ke Blog" di prediksi.html)
  firebase: {
  apiKey: "AIzaSyAZQuaa9qx4KZwFHPvk9ygJ_WphFnJ9Qnk",
  authDomain: "wb-prediction.firebaseapp.com",
  projectId: "wb-prediction",
  storageBucket: "wb-prediction.firebasestorage.app",
  messagingSenderId: "229482027147",
  appId: "1:229482027147:web:b960d808af5f39721bdc8e"
}
};

/* ===== Tombol "Aplikasi" (menu di toko.html & blog.html) -> buka link Toko yang aktif =====
   Aktif = tidak dikunci di admin scenangka (sama dengan tombol Toko Member).
   Pakai situs yang tadi dipilih lewat Toko Member kalau masih aktif, kalau tidak acak dari yang aktif.
   Kalau semua terkunci / gagal baca status: perilaku lama (./?app=1). Halaman lain tidak terpengaruh. */
(function () {
  'use strict';
  if (!/(^|\/)(toko|blog)(\.html)?$/.test(location.pathname)) return;
  var cache = null;

  function cfg() {
    var S = window.WB_STORE || {}, C = window.WB_CONFIG || {};
    return {
      links: C.TOKO_LINKS || S.tokoLinks || [],
      worker: C.WORKER || S.worker || '',
      acct: C.ACCT || 'scenangka-scenangka'
    };
  }
  function ambil(url) {
    return fetch(url, { cache: 'no-store' }).then(function (r) { return r.json(); });
  }
  /* hasil: objek status {id:false = terkunci}, atau null kalau gagal baca */
  function muat() {
    if (cache) return cache;
    var c = cfg();
    if (!c.worker) return Promise.resolve(null);
    var base = c.worker + '/' + c.acct;
    cache = ambil(base + '/logs').then(function (lg) {
      var mb = lg && lg.membersBin;
      if (!mb) return null;
      return ambil(base + '/' + mb).then(function (d) {
        var arr = Array.isArray(d) ? d : ((d && d.data) || []);
        var st = arr.find(function (m) { return m.id === '__SETTINGS__'; });
        return (st && st.tk) ? st.tk : {};
      });
    }).catch(function () { return null; }).then(function (r) {
      if (r === null) cache = null;   /* gagal: boleh coba lagi di klik berikutnya */
      return r;
    });
    return cache;
  }
  function pilih(status, links) {
    var buka = links.filter(function (l) { return status[l.id] !== false; });
    if (!buka.length) return null;
    var simpan = '';
    try { simpan = localStorage.getItem('wb_toko_situs') || ''; } catch (e) {}
    for (var i = 0; i < buka.length; i++) if (buka[i].id === simpan) return buka[i];
    return buka[Math.floor(Math.random() * buka.length)];
  }
  function cocok(a) {
    var h = a.getAttribute('href') || '';
    if (/[?&]app=1(&|$)/.test(h)) return true;
    return !!a.closest('nav,.nav') && a.textContent.trim().toLowerCase() === 'aplikasi';
  }

  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    var a = e.target && e.target.closest ? e.target.closest('a') : null;
    var links = cfg().links;
    if (!a || !links.length || !cocok(a)) return;
    e.preventDefault();
    var asal = a.href;
    a.style.opacity = '.6';
    muat().then(function (st) {
      var p = st ? pilih(st, links) : null;
      location.href = p ? p.url : asal;
    });
  }, true);

  document.addEventListener('DOMContentLoaded', muat);
})();
