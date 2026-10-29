// Config penyimpanan (Cloudflare Worker) - akun alifavif-cmd
// Satu Worker dipakai semua akun; data tiap akun dipisah lewat nama "account".
window.WB_STORE = {
  worker: 'https://steep-resonance-6a71.kjago7822.workers.dev',
  account: 'alifavif-cmd',
  // Link di akhir kopipasta trek (prediksi.html)
  siteUrl: 'https://angkahoky187-crypto.github.io/MASTER/',
  // Daftar link Toko Member (dipakai toko.html alifavif; kunci buka/tutup diatur dari Admin > tab Toko)
  // vip: true  = masuk Scen VIP (tombol Scen VIP muncul otomatis di toko.html). Tanpa vip = Scen Member biasa.
  // wa: '62...' (opsional) = pesan ACC untuk situs ini dikirim ke WhatsApp tersebut, bukan ke WhatsApp admin utama.
  tokoLinks: [
    { id: 'kjago7822',                    url: 'https://kjago7822.github.io/WB-PREDICTION-/' },
    { id: 'wgus543-hub',                  url: 'https://wgus543-hub.github.io/WB-PREDICTION-/' },
    { id: 'mamakeavif-star',              url: 'https://mamakeavif-star.github.io/WB-PREDICTION-/' },
    { id: 'adinealif-byte',               url: 'https://adinealif-byte.github.io/WB-PREDICTION-/' },
    { id: 'paitoangka1234-cpu',           url: 'https://paitoangka1234-cpu.github.io/WB-scen/', vip: true },
    { id: 'kpps33040420090144-creator',   url: 'https://kpps33040420090144-creator.github.io/WB-PREDICTION-/', vip: true },
    { id: 'bototomart787-png',            url: 'https://bototomart787-png.github.io/Scenangka/' }
  ]
};
