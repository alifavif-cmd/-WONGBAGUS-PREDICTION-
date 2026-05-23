/**
 * wb_data.js — WongBagus Prediction · Shared Data Module
 * ========================================================
 * Dipakai oleh SEMUA halaman: index.html, rekap_2d-1.html,
 * bola_merah.html, rekap_3d.html, rekap_4d.html, pola_sgp.html,
 * kalender_togel.html, bank_rumus.html, dll.
 *
 * CARA PAKAI (di tiap halaman, sebelum script utama):
 *   <script src="./wb_data.js"></script>
 *
 * API publik:
 *   WBData.getAll()            → { hk:{result,status,updated,name,...}, ..., _meta:{} }
 *   WBData.get(id)             → entry untuk 1 pasaran, atau null
 *   WBData.getResult(id)       → string 4-digit / '----' / null
 *   WBData.onUpdate(callback)  → register listener; dipanggil setiap data berubah
 *   WBData.offUpdate(callback) → hapus listener
 *   WBData.isFresh()           → true jika cache < 90 menit
 *   WBData.metaUpdated()       → string timestamp terakhir update
 *   WBData.MARKETS             → array definisi 65 pasaran (readonly)
 *   WBData.KEYWORD_MAP         → array keyword→id mapping
 *
 * index.html memanggil WBData._write(rj) setelah dapat data
 * dari result.json / paito-harian. Halaman lain HANYA membaca.
 */

(function(global) {
  'use strict';

  // ── Storage key ─────────────────────────────────────────────
  const CACHE_KEY   = 'wb_rj_v3';        // sama dg index.html lama
  const SHARED_KEY  = 'wb_shared_v1';    // kunci baru yg dipakai halaman lain
  const CACHE_TTL   = 90 * 60 * 1000;   // 90 menit

  // ── Internal state ──────────────────────────────────────────
  let _data   = null;   // object result.json terakhir
  let _ts     = 0;      // epoch ms saat data ditulis
  let _listeners = [];

  // ── 65 PASARAN definisi ─────────────────────────────────────
  const MARKETS = [
    // ASIA UTAMA
    {id:'hk',   flag:'🇭🇰',name:'Hongkong',       short:'HK',    time:'23:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-hongkong-pools/',         wb:'hongkong-pools'},
    {id:'hkl',  flag:'🇭🇰',name:'HK Lotto',       short:'HKL',   time:'23:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-hklotto/',                 wb:''},
    {id:'sgp',  flag:'🇸🇬',name:'Singapore',      short:'SGP',   time:'17:40',days:'Sen,Rab,Kam,Sab,Min', an:'/data-pengeluaran-togel-singapore/',       wb:'singapore'},
    {id:'sdy',  flag:'🇦🇺',name:'Sydney Pools',   short:'SDY',   time:'13:45',days:'Sen-Sab',      an:'/data-pengeluaran-togel-sydney-pools/',           wb:'sydney-pools'},
    {id:'sdl',  flag:'🇦🇺',name:'Sydney Lotto',   short:'SDL',   time:'13:45',days:'Sen-Sab',      an:'/data-pengeluaran-togel-sdlotto/',                wb:'sdlotto'},
    {id:'kam',  flag:'🇰🇭',name:'Kamboja',        short:'KAM',   time:'11:50',days:'Setiap Hari', an:'/data-pengeluaran-togel-magnum-cambodia/',         wb:'magnum-cambodia'},
    {id:'bull', flag:'🇳🇿',name:'Bullseye NZ',    short:'BULL',  time:'13:10',days:'Setiap Hari', an:'/data-pengeluaran-togel-bullseye/',                wb:'bullseye'},
    {id:'chn',  flag:'🇨🇳',name:'China Pools',    short:'CHN',   time:'15:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-chinapools/',              wb:'chinapools'},
    {id:'jpn',  flag:'🇯🇵',name:'Japan',          short:'JPN',   time:'17:20',days:'Setiap Hari', an:'/data-pengeluaran-togel-japan/',                   wb:'japan'},
    {id:'twn',  flag:'🇹🇼',name:'Taiwan',         short:'TWN',   time:'20:45',days:'Setiap Hari', an:'/data-pengeluaran-togel-taiwan/',                  wb:'taiwan'},
    {id:'pcso', flag:'🇵🇭',name:'PCSO',           short:'PCSO',  time:'20:10',days:'Setiap Hari', an:'/data-pengeluaran-togel-pcso/',                    wb:''},
    // TOTO MACAU
    {id:'mac1', flag:'🇲🇴',name:'Toto Macau 13',  short:'MAC13', time:'13:10',days:'Setiap Hari', an:'/data-pengeluaran-togel-toto-macau-1/',            wb:''},
    {id:'mac2', flag:'🇲🇴',name:'Toto Macau 16',  short:'MAC16', time:'16:10',days:'Setiap Hari', an:'/data-pengeluaran-togel-toto-macau-2/',            wb:''},
    {id:'mac3', flag:'🇲🇴',name:'Toto Macau 19',  short:'MAC19', time:'19:10',days:'Setiap Hari', an:'/data-pengeluaran-togel-toto-macau-3/',            wb:''},
    {id:'mac4', flag:'🇲🇴',name:'Toto Macau 22',  short:'MAC22', time:'22:10',days:'Setiap Hari', an:'/data-pengeluaran-togel-toto-macau-4/',            wb:''},
    {id:'mac5', flag:'🇲🇴',name:'Toto Macau 00',  short:'MAC00', time:'00:11',days:'Setiap Hari', an:'/data-pengeluaran-togel-toto-macau-5/',            wb:''},
    {id:'mac6', flag:'🇲🇴',name:'Toto Macau 23',  short:'MAC23', time:'23:10',days:'Setiap Hari', an:'/data-pengeluaran-togel-toto-macau-6/',            wb:''},
    // MOROCCO
    {id:'mrq3',  flag:'🇲🇦',name:'Morocco 03:00', short:'MRQ3',  time:'03:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-morocco-quatro-03-00-wib/', wb:''},
    {id:'mrq18', flag:'🇲🇦',name:'Morocco 18:00', short:'MRQ18', time:'18:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-morocco-quatro-18-00-wib/', wb:''},
    {id:'mrq21', flag:'🇲🇦',name:'Morocco 21:00', short:'MRQ21', time:'21:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-morocco-quatro-21-00-wib/', wb:''},
    {id:'mrq23', flag:'🇲🇦',name:'Morocco 23:59', short:'MRQ23', time:'23:59',days:'Setiap Hari', an:'/data-pengeluaran-togel-morocco-quatro-23-59-wib/', wb:''},
    // GERMANY
    {id:'ger',  flag:'🇩🇪',name:'Germany Plus5',  short:'GER',   time:'01:10',days:'Setiap Hari', an:'/data-pengeluaran-togel-germany-plus5/',           wb:''},
    // OREGON
    {id:'or4',  flag:'🇺🇸',name:'Oregon 04:00',   short:'OR4',   time:'04:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-oregon-04-00-wib/',        wb:''},
    {id:'or7',  flag:'🇺🇸',name:'Oregon 07:00',   short:'OR7',   time:'07:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-oregon-07-00-wib/',        wb:''},
    {id:'or10', flag:'🇺🇸',name:'Oregon 10:00',   short:'OR10',  time:'10:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-oregon-10-00-wib/',        wb:''},
    {id:'or13', flag:'🇺🇸',name:'Oregon 13:00',   short:'OR13',  time:'13:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-oregon-13-00-wib/',        wb:''},
    // NORTH CAROLINA
    {id:'ncd',  flag:'🇺🇸',name:'NC Day',         short:'NCD',   time:'03:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-north-carolina-day/',      wb:'north-carolina-day'},
    {id:'nce',  flag:'🇺🇸',name:'NC Evening',     short:'NCE',   time:'11:22',days:'Setiap Hari', an:'/data-pengeluaran-togel-north-carolina-evening/',  wb:''},
    // GEORGIA
    {id:'geom', flag:'🇺🇸',name:'Georgia Mid',    short:'GEOM',  time:'00:29',days:'Setiap Hari', an:'/data-pengeluaran-togel-georgia-midday/',          wb:''},
    {id:'geoe', flag:'🇺🇸',name:'Georgia Eve',    short:'GEOE',  time:'07:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-georgia-evening/',         wb:''},
    {id:'geon', flag:'🇺🇸',name:'Georgia Night',  short:'GEON',  time:'11:34',days:'Setiap Hari', an:'/data-pengeluaran-togel-georgia-night/',           wb:''},
    // TEXAS
    {id:'txd',  flag:'🇺🇸',name:'Texas Day',      short:'TXD',   time:'01:27',days:'Setiap Hari', an:'/data-pengeluaran-togel-texas-day/',               wb:''},
    {id:'txmr', flag:'🇺🇸',name:'Texas Morning',  short:'TXMR',  time:'22:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-texas-morning/',           wb:''},
    {id:'txe',  flag:'🇺🇸',name:'Texas Evening',  short:'TXE',   time:'09:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-texas-evening/',           wb:''},
    {id:'txn',  flag:'🇺🇸',name:'Texas Night',    short:'TXN',   time:'14:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-texas-night/',             wb:''},
    // NEW YORK
    {id:'nyd',  flag:'🇺🇸',name:'New York Mid',   short:'NYD',   time:'01:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-new-york-midday/',         wb:''},
    {id:'nye',  flag:'🇺🇸',name:'New York Eve',   short:'NYE',   time:'10:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-new-york-evening/',        wb:''},
    // NEW JERSEY
    {id:'njm',  flag:'🇺🇸',name:'NJ Midday',      short:'NJM',   time:'01:57',days:'Setiap Hari', an:'/data-pengeluaran-togel-new-jersey-midday/',       wb:''},
    {id:'nje',  flag:'🇺🇸',name:'NJ Evening',     short:'NJE',   time:'10:57',days:'Setiap Hari', an:'/data-pengeluaran-togel-new-jersey-evening/',      wb:''},
    // FLORIDA
    {id:'flm',  flag:'🇺🇸',name:'Florida Mid',    short:'FLM',   time:'01:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-florida-midday/',          wb:''},
    {id:'fle',  flag:'🇺🇸',name:'Florida Eve',    short:'FLE',   time:'11:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-florida-evening/',         wb:''},
    // ILLINOIS
    {id:'ilm',  flag:'🇺🇸',name:'Illinois Mid',   short:'ILM',   time:'02:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-illinois-midday/',         wb:''},
    {id:'ile',  flag:'🇺🇸',name:'Illinois Eve',   short:'ILE',   time:'11:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-illinois-evening/',        wb:''},
    // INDIANA
    {id:'indm', flag:'🇺🇸',name:'Indiana Mid',    short:'INDM',  time:'02:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-indiana-midday/',          wb:''},
    {id:'inde', flag:'🇺🇸',name:'Indiana Eve',    short:'INDE',  time:'11:29',days:'Setiap Hari', an:'/data-pengeluaran-togel-indiana-evening/',         wb:''},
    // KENTUCKY
    {id:'kym',  flag:'🇺🇸',name:'Kentucky Mid',   short:'KYM',   time:'01:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-kentucky-midday/',         wb:''},
    {id:'kye',  flag:'🇺🇸',name:'Kentucky Eve',   short:'KYE',   time:'10:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-kentucky-evening/',        wb:''},
    // MARYLAND
    {id:'mdm',  flag:'🇺🇸',name:'Maryland Mid',   short:'MDM',   time:'01:55',days:'Setiap Hari', an:'/data-pengeluaran-togel-maryland-midday/',         wb:''},
    {id:'mde',  flag:'🇺🇸',name:'Maryland Eve',   short:'MDE',   time:'10:57',days:'Setiap Hari', an:'/data-pengeluaran-togel-maryland-evening/',        wb:''},
    // MICHIGAN
    {id:'mim',  flag:'🇺🇸',name:'Michigan Mid',   short:'MIM',   time:'01:28',days:'Setiap Hari', an:'/data-pengeluaran-togel-michigan-midday/',         wb:''},
    {id:'mie',  flag:'🇺🇸',name:'Michigan Eve',   short:'MIE',   time:'10:28',days:'Setiap Hari', an:'/data-pengeluaran-togel-michigan-evening/',        wb:''},
    // MISSOURI
    {id:'mom',  flag:'🇺🇸',name:'Missouri Mid',   short:'MOM',   time:'01:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-missouri-midday/',         wb:''},
    {id:'moe',  flag:'🇺🇸',name:'Missouri Eve',   short:'MOE',   time:'10:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-missouri-evening/',        wb:''},
    // WASHINGTON DC
    {id:'wdm',  flag:'🇺🇸',name:'WDC Midday',     short:'WDM',   time:'01:50',days:'Setiap Hari', an:'/data-pengeluaran-togel-washington-dc-midday/',    wb:''},
    {id:'wde',  flag:'🇺🇸',name:'WDC Evening',    short:'WDE',   time:'10:50',days:'Setiap Hari', an:'/data-pengeluaran-togel-washington-dc-evening/',   wb:''},
    // CONNECTICUT
    {id:'ctd',  flag:'🇺🇸',name:'Connecticut Day', short:'CTD',  time:'02:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-connecticut-day/',         wb:''},
    {id:'ctn',  flag:'🇺🇸',name:'Connecticut Night',short:'CTN', time:'11:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-connecticut-night/',        wb:''},
    // VIRGINIA
    {id:'vad',  flag:'🇺🇸',name:'Virginia Day',   short:'VAD',   time:'02:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-virginia-day/',            wb:''},
    {id:'van',  flag:'🇺🇸',name:'Virginia Night', short:'VAN',   time:'11:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-virginia-night/',           wb:''},
    // TENNESSEE
    {id:'tnm',  flag:'🇺🇸',name:'Tennessee Mid',  short:'TNM',   time:'01:29',days:'Setiap Hari', an:'/data-pengeluaran-togel-tennesse-midday/',         wb:''},
    {id:'tne',  flag:'🇺🇸',name:'Tennessee Eve',  short:'TNE',   time:'10:29',days:'Setiap Hari', an:'/data-pengeluaran-togel-tennesse-evening/',        wb:''},
    {id:'tnmr', flag:'🇺🇸',name:'Tennessee Morning',short:'TNMR',time:'22:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-tennesse-morning/',        wb:''},
    // LAINNYA
    {id:'cal',  flag:'🇺🇸',name:'California',     short:'CAL',   time:'10:00',days:'Setiap Hari', an:'/data-pengeluaran-togel-california/',              wb:''},
    {id:'wie',  flag:'🇺🇸',name:'Wisconsin Eve',  short:'WIE',   time:'10:30',days:'Setiap Hari', an:'/data-pengeluaran-togel-wisconsin-evening/',       wb:''},
  ];

  // ── KEYWORD MAP (untuk parse paito-harian) ──────────────────
  const KEYWORD_MAP = [
    ['hongkong pool','hk'],['hk pools','hk'],['hk lotto','hkl'],['hklotto','hkl'],
    ['singapore','sgp'],
    ['sydney pools','sdy'],['sydney pool','sdy'],['sydney lotto','sdl'],['sdlotto','sdl'],
    ['magnum cambodia','kam'],['kamboja','kam'],['cambodia','kam'],
    ['bullseye','bull'],
    ['china pool','chn'],['chinapool','chn'],
    ['japan','jpn'],['taiwan','twn'],['pcso','pcso'],
    ['toto macau 1','mac1'],['macau 13','mac1'],
    ['toto macau 2','mac2'],['macau 16','mac2'],
    ['toto macau 3','mac3'],['macau 19','mac3'],
    ['toto macau 4','mac4'],['macau 22','mac4'],
    ['toto macau 5','mac5'],['macau 00','mac5'],
    ['toto macau 6','mac6'],['macau 23','mac6'],
    ['morocco quatro 03','mrq3'],['morocco 03','mrq3'],
    ['morocco quatro 18','mrq18'],['morocco 18','mrq18'],
    ['morocco quatro 21','mrq21'],['morocco 21','mrq21'],
    ['morocco quatro 23','mrq23'],['morocco 23','mrq23'],
    ['germany','ger'],
    ['oregon 04','or4'],['oregon 07','or7'],['oregon 10','or10'],['oregon 13','or13'],
    ['north carolina day','ncd'],['nc day','ncd'],
    ['north carolina evening','nce'],['nc evening','nce'],
    ['georgia midday','geom'],['georgia mid','geom'],
    ['georgia evening','geoe'],['georgia eve','geoe'],
    ['georgia night','geon'],
    ['texas morning','txmr'],['texas day','txd'],['texas evening','txe'],['texas night','txn'],
    ['new york midday','nyd'],['new york evening','nye'],
    ['new jersey midday','njm'],['nj midday','njm'],
    ['new jersey evening','nje'],['nj evening','nje'],
    ['florida midday','flm'],['florida evening','fle'],
    ['illinois midday','ilm'],['illinois evening','ile'],
    ['indiana midday','indm'],['indiana evening','inde'],
    ['kentucky midday','kym'],['kentucky evening','kye'],
    ['maryland midday','mdm'],['maryland evening','mde'],
    ['michigan midday','mim'],['michigan evening','mie'],
    ['missouri midday','mom'],['missouri evening','moe'],
    ['washington dc midday','wdm'],['wdc midday','wdm'],
    ['washington dc evening','wde'],['wdc evening','wde'],
    ['connecticut day','ctd'],['connecticut night','ctn'],
    ['virginia day','vad'],['virginia night','van'],
    ['tennesse midday','tnm'],['tennessee midday','tnm'],
    ['tennesse evening','tne'],['tennessee evening','tne'],
    ['tennesse morning','tnmr'],['tennessee morning','tnmr'],
    ['california','cal'],['wisconsin evening','wie'],
  ];

  // ── Result.json URLs (fallback cascade) ─────────────────────
  const RESULT_JSON_URLS = [
    './result.json',
    'https://alifavif-cmd.github.io/-WONGBAGUS-PREDICTION-/result.json',
    'https://raw.githubusercontent.com/alifavif-cmd/-WONGBAGUS-PREDICTION-/main/result.json',
  ];

  // ── Paito Harian URL ─────────────────────────────────────────
  const PAITO_HARIAN_URL = 'https://angkanet18.com/paito-harian/';

  // ── CORS proxy list ──────────────────────────────────────────
  const PROXIES = [
    u => 'https://api.allorigins.win/get?url=' + encodeURIComponent(u),
    u => 'https://corsproxy.io/?' + encodeURIComponent(u),
    u => 'https://api.codetabs.com/v1/proxy?quest=' + encodeURIComponent(u),
  ];

  // ── Helpers ──────────────────────────────────────────────────
  const FAKE_PAT = [
    /^1234$/,/^2345$/,/^3456$/,/^4567$/,/^5678$/,
    /^6789$/,/^7890$/,/^8901$/,/^9012$/,/^0123$/,/^(\d)\1{3}$/,
  ];

  function isFake(r) {
    if (!/^\d{4}$/.test(r)) return true;
    const n = parseInt(r, 10);
    if (n >= 1800 && n <= 2099) return true;
    return FAKE_PAT.some(p => p.test(r));
  }

  function matchMarket(text) {
    const tl = text.toLowerCase();
    for (const [kw, key] of KEYWORD_MAP) { if (tl.includes(kw)) return key; }
    return null;
  }

  // ── localStorage helpers ─────────────────────────────────────
  function _save(rj) {
    try {
      const payload = { ts: Date.now(), rj };
      localStorage.setItem(CACHE_KEY,  JSON.stringify(payload));
      localStorage.setItem(SHARED_KEY, JSON.stringify(payload));
    } catch (e) {}
  }

  function _load() {
    // Coba SHARED_KEY dulu (lebih fresh), lalu CACHE_KEY lama
    for (const key of [SHARED_KEY, CACHE_KEY]) {
      try {
        const raw = localStorage.getItem(key);
        if (!raw) continue;
        const { ts, rj } = JSON.parse(raw);
        if (Date.now() - ts > CACHE_TTL) continue;
        return { ts, rj };
      } catch (e) {}
    }
    return null;
  }

  // ── Internal write (dipanggil index.html) ────────────────────
  function _write(rj) {
    if (!rj || typeof rj !== 'object') return;
    _data = rj;
    _ts   = Date.now();
    _save(rj);
    _notifyListeners();
  }

  // ── Notifikasi listeners ─────────────────────────────────────
  function _notifyListeners() {
    for (const cb of _listeners) {
      try { cb(_data); } catch (e) {}
    }
  }

  // ── Fetch result.json ─────────────────────────────────────────
  async function _fetchResultJson(url) {
    try {
      const res = await Promise.race([
        fetch(url, { cache: 'no-cache' }),
        new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), 10000)),
      ]);
      if (!res.ok) return null;
      return await res.json();
    } catch (e) { return null; }
  }

  // ── Fetch via CORS proxy ──────────────────────────────────────
  async function _proxyFetch(url) {
    for (const makeProxy of PROXIES) {
      try {
        const res = await Promise.race([
          fetch(makeProxy(url)),
          new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), 10000)),
        ]);
        if (!res.ok) continue;
        const data = await res.json();
        const html = typeof data === 'string' ? data : (data.contents || data.data || '');
        if (html && html.length > 100) return html;
      } catch (e) {}
    }
    return null;
  }

  // ── Parse paito-harian HTML → {id: result4digit} ─────────────
  function _parsePaitoHarian(html) {
    const found = {};
    if (!html || html.length < 500) return found;
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    // Strategy 1: container dengan heading
    const containers = [...doc.querySelectorAll('section,div,article,li')].filter(el => {
      const cls = (el.className || '').toLowerCase();
      return /market|pasaran|paito|result|item|card|pool/.test(cls);
    });
    for (const sec of containers) {
      const hEl = sec.querySelector('h1,h2,h3,h4,h5,strong');
      if (!hEl) continue;
      const key = matchMarket(hEl.textContent || '');
      if (!key || found[key]) continue;
      for (const tag of sec.querySelectorAll('span,td,div,b,p')) {
        const t = (tag.textContent || '').trim();
        if (/^\d{4}$/.test(t) && !isFake(t)) { found[key] = t; break; }
      }
    }

    // Strategy 2: .paito-row-item grouped by parent
    if (Object.keys(found).length < 10) {
      const rowMap = new Map();
      for (const item of doc.querySelectorAll('.paito-row-item')) {
        const pid = item.parentElement;
        if (!rowMap.has(pid)) rowMap.set(pid, { texts: [], result: null });
        const t = (item.textContent || '').trim();
        rowMap.get(pid).texts.push(t);
        if (!rowMap.get(pid).result && /^\d{4}$/.test(t) && !isFake(t))
          rowMap.get(pid).result = t;
      }
      for (const [, info] of rowMap) {
        if (!info.result) continue;
        const key = matchMarket(info.texts.join(' '));
        if (key && !found[key]) found[key] = info.result;
      }
    }

    // Strategy 3: scan tr/li
    if (Object.keys(found).length < 5) {
      let count = 0;
      for (const block of doc.querySelectorAll('tr,li')) {
        if (++count > 3000) break;
        const t = (block.textContent || '').trim();
        if (!/^\d{4}$/.test(t) || isFake(t)) continue;
        const pTxt = block.parentElement ? (block.parentElement.textContent || '') : '';
        const key = matchMarket(pTxt);
        if (key && !found[key]) found[key] = t;
      }
    }
    return found;
  }

  /**
   * fetchFromPaitoHarian — halaman lain bisa panggil ini
   * untuk refresh data tanpa perlu buka index.html.
   * Fallback: result.json → paito-harian → data lama cache.
   */
  async function fetchFromPaitoHarian() {
    // 1. Coba result.json
    for (const url of RESULT_JSON_URLS) {
      const rj = await _fetchResultJson(url + '?t=' + Date.now());
      if (rj && (rj._meta || Object.keys(rj).length > 5)) {
        _write(rj);
        console.log('[WBData] result.json OK:', url);
        return rj;
      }
    }

    // 2. Coba paito-harian
    console.log('[WBData] Fetching paito-harian...');
    const html = await _proxyFetch(PAITO_HARIAN_URL);
    const found = _parsePaitoHarian(html || '');
    const count = Object.keys(found).length;
    console.log('[WBData] paito-harian:', count, 'pasaran');

    if (count >= 5) {
      const now = new Date().toLocaleTimeString('id-ID');
      const rj = {
        _meta: { updated: now, date: '', total: MARKETS.length, source: 'paito-harian' },
      };
      for (const m of MARKETS) {
        const r = found[m.id];
        if (r && /^\d{4}$/.test(r) && !isFake(r)) {
          rj[m.id] = { result: r, status: 'sudah', updated: now, name: m.name };
        }
      }
      _write(rj);
      return rj;
    }

    // 3. Return data cache lama (mungkin stale, tapi lebih baik dari kosong)
    return _data;
  }

  // ── Init: muat cache saat script dimuat ─────────────────────
  (function _init() {
    const cached = _load();
    if (cached) {
      _data = cached.rj;
      _ts   = cached.ts;
      console.log('[WBData] Cache loaded, age:', Math.round((Date.now() - _ts) / 60000), 'menit');
    }

    // Listen untuk update dari tab lain (index.html di tab berbeda)
    try {
      window.addEventListener('storage', function(e) {
        if (e.key !== SHARED_KEY) return;
        try {
          const { ts, rj } = JSON.parse(e.newValue);
          if (ts > _ts) {
            _data = rj;
            _ts   = ts;
            console.log('[WBData] Data updated from another tab');
            _notifyListeners();
          }
        } catch (err) {}
      });
    } catch (e) {}
  })();

  // ── Public API ───────────────────────────────────────────────
  global.WBData = {
    /** Semua data result.json terakhir */
    getAll() { return _data; },

    /** Entry untuk 1 pasaran, atau null */
    get(id) { return _data ? (_data[id] || null) : null; },

    /** Result 4-digit untuk 1 pasaran, atau '----' / null */
    getResult(id) {
      const e = this.get(id);
      if (!e) return null;
      const r = String(e.result || '');
      return /^\d{4}$/.test(r) ? r : '----';
    },

    /** Register listener dipanggil setiap data berubah */
    onUpdate(cb) {
      if (typeof cb === 'function' && !_listeners.includes(cb))
        _listeners.push(cb);
    },

    /** Hapus listener */
    offUpdate(cb) {
      _listeners = _listeners.filter(x => x !== cb);
    },

    /** true jika cache ada dan < 90 menit */
    isFresh() { return !!_data && (Date.now() - _ts < CACHE_TTL); },

    /** Timestamp update terakhir */
    metaUpdated() { return _data && _data._meta ? _data._meta.updated : ''; },

    /** Fetch baru dari result.json / paito-harian (untuk halaman lain) */
    async refresh() { return fetchFromPaitoHarian(); },

    /** Internal: dipakai index.html untuk push data segar */
    _write,

    /** Definisi 65 pasaran */
    MARKETS,

    /** Keyword map untuk parse paito-harian */
    KEYWORD_MAP,

    /** CORS proxy fetch (kalau halaman lain perlu) */
    _proxyFetch,

    /** Parse paito-harian HTML */
    _parsePaitoHarian,

    /** Helper isFake */
    isFake,

    /** Helper matchMarket */
    matchMarket,
  };

})(window);
