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
  apiKey: "AIzaSyBgSWlU9xkG-A3seitPy9zI_743aeLIEFo",
  authDomain: "komunikasi-e593d.firebaseapp.com",
  projectId: "komunikasi-e593d",
  storageBucket: "komunikasi-e593d.firebasestorage.app",
  messagingSenderId: "509726825544",
  appId: "1:509726825544:web:02c5e6b9100ea7954b4c7d"
}
};
