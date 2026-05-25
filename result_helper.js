/**
 * result_helper.js — Modul universal untuk baca result.json
 * Dipakai oleh semua HTML: isi otomatis, load history, paito, dll.
 *
 * CARA PAKAI di HTML mana saja:
 *   <script src="result_helper.js"></script>
 *
 * Atau copy paste blok <script> ini langsung ke dalam HTML.
 *
 * ─── API ────────────────────────────────────────────────────
 *  ResultHelper.load()                     → Promise<data>
 *  ResultHelper.getResult(key)             → {result, tgl, status, name, updated, history}
 *  ResultHelper.getHistory(key, n=30)      → [{date, result, 2d, 3d, as, kop, kp, ek}, ...]
 *  ResultHelper.isiOtomatis(key, fields)   → isi input secara otomatis
 *  ResultHelper.getAllPasaran()            → [{key, name, result, status}, ...]
 * ────────────────────────────────────────────────────────────
 */

const ResultHelper = (() => {

  // ─── Ganti URL ini kalau result.json ada di GitHub Pages ───
  const RESULT_URL = './result.json';
  // ────────────────────────────────────────────────────────────

  let _cache = null;
  let _loadTime = 0;
  const CACHE_TTL = 60_000; // 60 detik

  /** Load result.json (cache 60 detik) */
  async function load(force = false) {
    const now = Date.now();
    if (!force && _cache && (now - _loadTime) < CACHE_TTL) return _cache;
    try {
      const res = await fetch(RESULT_URL + '?t=' + now);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      _cache = await res.json();
      _loadTime = now;
      return _cache;
    } catch (e) {
      console.warn('[ResultHelper] Gagal load result.json:', e.message);
      return _cache || {};
    }
  }

  /**
   * Pecah 4D → komponen
   * Contoh: '3847' → {d4:'3847', d3:'847', d2:'47', as:'3', kop:'8', kp:'4', ek:'7'}
   */
  function pecah4D(r) {
    if (!r || !/^\d{4}$/.test(r)) return null;
    return {
      d4: r,
      d3: r.slice(1),
      d2: r.slice(2),
      as:  r[0],
      kop: r[1],
      kp:  r[2],
      ek:  r[3],
    };
  }

  /**
   * Format tanggal "2026-05-25" → "25/05" atau "25 Mei"
   */
  function fmtDate(dateStr, mode = 'short') {
    if (!dateStr) return '-';
    const [y, m, d] = dateStr.split('-').map(Number);
    if (mode === 'short') return `${String(d).padStart(2,'0')}/${String(m).padStart(2,'0')}`;
    const bulan = ['','Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];
    return `${d} ${bulan[m]}`;
  }

  // ─── Public API ─────────────────────────────────────────────

  /** Ambil data satu pasaran */
  async function getResult(key) {
    const data = await load();
    return data[key] || null;
  }

  /**
   * Ambil history satu pasaran, enriched dengan komponen 4D.
   * Return array [{date, result, d3, d2, as, kop, kp, ek, tgl_fmt}, ...]
   * Sudah sorted descending tanggal.
   */
  async function getHistory(key, n = 30) {
    const data = await load();
    const entry = data[key];
    if (!entry) return [];

    const history = (entry.history || []).slice(0, n);

    // Kalau history masih kosong tapi ada result hari ini → seed 1 entry
    if (history.length === 0 && entry.result && /^\d{4}$/.test(entry.result)) {
      const today = data._meta?.today_str || new Date().toISOString().slice(0,10);
      history.push({ date: today, result: entry.result });
    }

    return history.map(h => {
      const p = pecah4D(h.result) || {};
      return {
        date:     h.date,
        tgl_fmt:  fmtDate(h.date),
        result:   h.result || '----',
        d4:       p.d4 || '----',
        d3:       p.d3 || '---',
        d2:       p.d2 || '--',
        as:       p.as  || '-',
        kop:      p.kop || '-',
        kp:       p.kp  || '-',
        ek:       p.ek  || '-',
      };
    });
  }

  /**
   * Isi Otomatis — isi input element berdasarkan result & history.
   *
   * @param {string} key   - key pasaran (misal 'hk', 'sgp')
   * @param {object} fields - mapping nama field → CSS selector
   *   Contoh:
   *   {
   *     result4d: '#inp4d',          // result 4D hari ini
   *     result3d: '#inp3d',          // 3D
   *     result2d: '#inp2d',          // 2D
   *     as:       '#inpAs',          // angka AS
   *     kop:      '#inpKop',
   *     kp:       '#inpKp',
   *     ek:       '#inpEk',
   *     // Array history: isi berurutan dari index 0 (terbaru)
   *     history4d: ['#h1','#h2','#h3'],  // 4D dari history[0], [1], [2]
   *     history2d: ['#d1','#d2','#d3'],  // 2D dari history
   *   }
   * @param {object} opts
   *   {
   *     historyIndex: 0,   // kalau mau ambil history ke-N, bukan hari ini
   *     trigger: 'input',  // event di-dispatch setelah isi (default: 'input')
   *   }
   */
  async function isiOtomatis(key, fields = {}, opts = {}) {
    const data    = await load();
    const entry   = data[key];
    if (!entry) {
      console.warn('[ResultHelper] Pasaran tidak ditemukan:', key);
      return false;
    }

    const history = await getHistory(key);
    const triggerEvent = opts.trigger ?? 'input';

    function setVal(selector, value) {
      if (!selector || !value) return;
      const els = typeof selector === 'string'
        ? document.querySelectorAll(selector)
        : [selector];
      els.forEach(el => {
        if (!el) return;
        el.value = value;
        el.dispatchEvent(new Event(triggerEvent, {bubbles: true}));
      });
    }

    // ── Isi result hari ini ──
    const todayParts = pecah4D(entry.result);
    if (todayParts) {
      setVal(fields.result4d, todayParts.d4);
      setVal(fields.result3d, todayParts.d3);
      setVal(fields.result2d, todayParts.d2);
      setVal(fields.as,       todayParts.as);
      setVal(fields.kop,      todayParts.kop);
      setVal(fields.kp,       todayParts.kp);
      setVal(fields.ek,       todayParts.ek);
    }

    // ── Isi history array ──
    if (fields.history4d) {
      fields.history4d.forEach((sel, i) => {
        setVal(sel, history[i]?.d4 || '');
      });
    }
    if (fields.history3d) {
      fields.history3d.forEach((sel, i) => {
        setVal(sel, history[i]?.d3 || '');
      });
    }
    if (fields.history2d) {
      fields.history2d.forEach((sel, i) => {
        setVal(sel, history[i]?.d2 || '');
      });
    }
    if (fields.historyEk) {
      fields.historyEk.forEach((sel, i) => {
        setVal(sel, history[i]?.ek || '');
      });
    }

    // ── Isi dari historyIndex (kalau butuh data kemarin, dll) ──
    if (opts.historyIndex !== undefined && history[opts.historyIndex]) {
      const hp = history[opts.historyIndex];
      setVal(fields.idxResult4d, hp.d4);
      setVal(fields.idxResult3d, hp.d3);
      setVal(fields.idxResult2d, hp.d2);
    }

    console.log(`[ResultHelper] isiOtomatis [${key}] selesai`, entry.result);
    return true;
  }

  /**
   * Ambil semua pasaran (untuk dropdown / select)
   * Return [{key, name, result, status, updated}, ...] sorted by name
   */
  async function getAllPasaran() {
    const data = await load();
    return Object.entries(data)
      .filter(([k]) => !k.startsWith('_'))
      .map(([key, v]) => ({
        key,
        name:    v.name    || key.toUpperCase(),
        result:  v.result  || '----',
        status:  v.status  || 'belum',
        updated: v.updated || '-',
        histLen: (v.history || []).length,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  /** Invalidate cache (paksa reload) */
  function clearCache() { _cache = null; _loadTime = 0; }

  // Expose
  return { load, getResult, getHistory, isiOtomatis, getAllPasaran, clearCache, pecah4D, fmtDate };

})();

// ─── Contoh pemakaian di HTML (hapus setelah paham) ─────────
//
// 1. Isi 4D + 2D + ekor dari pasaran HK ke input yang ada:
//    ResultHelper.isiOtomatis('hk', {
//      result4d: '#inp4d',
//      result2d: '#inp2d',
//      ek:       '#inpEkor',
//    });
//
// 2. Isi 30 input history 2D berurutan:
//    ResultHelper.isiOtomatis('sgp', {
//      history2d: Array.from({length:30}, (_,i) => `#h2d_${i}`),
//    });
//
// 3. Load history untuk bikin tabel:
//    const hist = await ResultHelper.getHistory('sgp', 30);
//    hist.forEach(row => console.log(row.tgl_fmt, row.d4, row.d2));
//
// 4. Isi dropdown pasaran:
//    const list = await ResultHelper.getAllPasaran();
//    const sel = document.querySelector('#selPasaran');
//    list.forEach(p => {
//      sel.innerHTML += `<option value="${p.key}">${p.name} — ${p.result}</option>`;
//    });
// ────────────────────────────────────────────────────────────
