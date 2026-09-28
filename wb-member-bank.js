/**
 * wb-member-bank.js
 * ─────────────────────────────────────────────────────────────────────
 * Bank rumus PER-MEMBER *dan* PER-APLIKASI (scan1..scan5), disimpan di
 * SERVER (JSONBin) — bukan di localStorage HP. Artinya: login dari HP
 * manapun pakai akun yang sama, bank rumusnya ikut kebawa.
 *
 * Data disimpan sebagai field "banks" di dalam record member itu sendiri,
 * di bin member yang SAMA dipakai index.html (BIN_MEMBERS) — jadi gak
 * perlu bikin bin baru lagi.
 *
 * WAJIB: taruh <script> kecil SEBELUM file ini yang isinya:
 *   window.WB_JSONBIN_CONFIG = { key: 'ACCESS_KEY_SITUS_INI', bin: 'BIN_MEMBERS_SITUS_INI' };
 * (nilai key & bin HARUS SAMA PERSIS dengan yang dipakai index.html situs ini,
 *  biar baca/tulis ke bin member yang sama.)
 *
 * Cara pakai di halaman scan (SEKARANG ASYNC — pakai .then() atau await!):
 *   WB_BANK.get('scan1').then(data => ...)
 *   await WB_BANK.set(data, 'scan1')
 *   await WB_BANK.add(item, 'scan1')
 *   await WB_BANK.clear('scan1')
 *   WB_BANK.currentId()   ← ini masih sinkron (baca sesi login lokal)
 * ─────────────────────────────────────────────────────────────────────
 */

(function(global){

  // Sama persis dengan skema di index.html: sesi login di-scope per-situs
  // (domain + folder repo), biar gak ketuker walau ada beberapa situs
  // WongBagus di akun GitHub yang sama.
  const WB_SITE_ID   = location.hostname + '/' + (location.pathname.split('/')[1] || '');
  const WB_LOGIN_KEY = 'wb_logged_member__' + WB_SITE_ID;

  function currentMemberId(){
    try{
      const raw = localStorage.getItem(WB_LOGIN_KEY);
      if(!raw) return 'guest';
      const obj = JSON.parse(raw);
      return (obj.id || obj.phone || 'guest');
    }catch(e){ return 'guest'; }
  }

  function currentMemberName(){
    try{
      const raw = localStorage.getItem(WB_LOGIN_KEY);
      if(!raw) return 'Guest';
      return JSON.parse(raw).name || 'Member';
    }catch(e){ return 'Member'; }
  }

  function cfg(){
    const c = global.WB_JSONBIN_CONFIG;
    if(!c || !c.key || !c.bin){
      throw new Error('WB_JSONBIN_CONFIG belum di-set. Cek <script> config sebelum wb-member-bank.js di <head>.');
    }
    return { key: c.key, bin: c.bin, base: c.base || 'https://api.jsonbin.io/v3/b' };
  }

  async function fetchMembers(){
    const c = cfg();
    const r = await fetch(`${c.base}/${c.bin}/latest`, { headers: { 'X-Access-Key': c.key } });
    if(!r.ok) throw new Error('Gagal ambil data member (HTTP '+r.status+')');
    const d = await r.json();
    if(!d || !d.record) return [];
    return Array.isArray(d.record) ? d.record : (d.record.data || []);
  }

  async function saveMembers(list){
    const c = cfg();
    const r = await fetch(`${c.base}/${c.bin}`, {
      method: 'PUT',
      headers: { 'X-Access-Key': c.key, 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: list })
    });
    if(!r.ok) throw new Error('Gagal simpan bank ke server (HTTP '+r.status+')');
  }

  // Cache in-memory per page-load, biar gak fetch berkali-kali tiap get()
  let _cache = null;
  let _cachePromise = null;
  async function loadCached(){
    if(_cache) return _cache;
    if(!_cachePromise) _cachePromise = fetchMembers().then(list => { _cache = list; return list; });
    return _cachePromise;
  }
  function invalidateCache(){ _cache = null; _cachePromise = null; }

  function findMember(list, memberId){
    const mid = memberId || currentMemberId();
    return list.find(m => m.id===mid || m.phone===mid);
  }

  async function bankGet(appId, memberId){
    try{
      const list = await loadCached();
      const m = findMember(list, memberId);
      const app = appId || 'default';
      return (m && m.banks && m.banks[app]) || [];
    }catch(e){ console.warn('[WB_BANK] gagal ambil bank:', e); return []; }
  }

  // Pangkas trekRows SEMUA member & SEMUA app (bukan cuma yang lagi disimpan),
  // biar bin yang sudah kepenuhan ikut mengecil di setiap kali ada yang simpan.
  const SERVER_TREK_CAP = 20;
  function trimAllBanks(list){
    list.forEach(m=>{
      if(!m || !m.banks) return;
      Object.keys(m.banks).forEach(app=>{
        const arr = m.banks[app];
        if(!Array.isArray(arr)) return;
        m.banks[app] = arr.map(item=>{
          if(!item || !Array.isArray(item.trekRows) || item.trekRows.length<=SERVER_TREK_CAP) return item;
          return { ...item, trekRows: item.trekRows.slice(-SERVER_TREK_CAP) };
        });
      });
    });
    return list;
  }

  async function bankSet(data, appId, memberId){
    const list = await fetchMembers(); // ambil FRESH biar gak nimpa perubahan lain yang barusan terjadi
    const mid = memberId || currentMemberId();
    let idx = list.findIndex(m => m.id===mid || m.phone===mid);
    if(idx===-1){
      // Admin gak ada di daftar member — bikinkan record khusus (disembunyikan dari daftar member)
      if(mid==='ADMIN'){ list.push({ id:'ADMIN', name:'Admin', banks:{} }); idx = list.length-1; }
      else throw new Error('Member tidak ditemukan di server (mungkin belum login / akun beda situs)');
    }
    const app = appId || 'default';
    list[idx].banks = list[idx].banks || {};
    if(data===null) delete list[idx].banks[app]; else list[idx].banks[app] = data || [];
    trimAllBanks(list);
    await saveMembers(list);
    invalidateCache();
  }

  async function bankAdd(item, appId, memberId){
    const bank = await bankGet(appId, memberId);
    const isDup = bank.some(b =>
      b.formula === item.formula &&
      (b.wbId||b.pasaran) === (item.wbId||item.pasaran) &&
      b.jenis === item.jenis
    );
    if(isDup) return false;
    bank.unshift({...item, savedAt: new Date().toISOString()});
    await bankSet(bank, appId, memberId);
    return true;
  }

  async function bankClear(appId, memberId){
    await bankSet([], appId, memberId);
  }

  async function bankListApps(memberId){
    try{
      const list = await loadCached();
      const m = findMember(list, memberId);
      return (m && m.banks) ? Object.keys(m.banks) : [];
    }catch(e){ return []; }
  }

  async function bankCountAll(memberId){
    const apps = await bankListApps(memberId);
    let sum = 0;
    for(const a of apps) sum += (await bankGet(a, memberId)).length;
    return sum;
  }


  // ══════════════════════════════════════════════════════════════
  // LAYER SINKRON — buat halaman scan yang kodenya sinkron.
  // Bank member dimuat SEKALI ke cache saat halaman dibuka; simpan
  // langsung update cache lalu dikirim ke server lewat antrean
  // (berurutan, biar dua simpan cepat tidak saling timpa).
  //   WB_BANK.onReady(cb)         → cb dipanggil setelah bank termuat
  //   WB_BANK.getSync(appId)      → ambil bank dari cache
  //   WB_BANK.setSync(data,appId) → simpan (cache + server)
  //   WB_BANK.clearSync(appId)    → hapus bank appId sepenuhnya
  //   WB_BANK.listAppsSync()      → daftar appId yang punya bank
  // ══════════════════════════════════════════════════════════════
  let _mine = {};
  let _loadOk = false, _isReady = false;
  const _readyCbs = [];
  let _queue = Promise.resolve();

  function bankToast(msg){
    try{
      let el = document.getElementById('wb-bank-toast');
      if(!el){
        el = document.createElement('div');
        el.id = 'wb-bank-toast';
        el.style.cssText = 'position:fixed;left:50%;bottom:56px;transform:translateX(-50%);z-index:100000;background:#7f1d1d;color:#fff;padding:8px 14px;border-radius:8px;font-size:12px;font-weight:700;max-width:90%;text-align:center;box-shadow:0 2px 10px rgba(0,0,0,.4)';
        document.body.appendChild(el);
      }
      el.textContent = msg; el.style.display = 'block';
      clearTimeout(el._t); el._t = setTimeout(()=>{ el.style.display='none'; }, 4500);
    }catch(e){}
  }

  async function preload(){
    const mid = currentMemberId();
    try{
      if(mid !== 'guest'){
        const list = await fetchMembers();
        const m = findMember(list, mid);
        _mine = (m && m.banks) ? JSON.parse(JSON.stringify(m.banks)) : {};
        _loadOk = true;
      }
    }catch(e){
      console.warn('[WB_BANK] gagal muat bank:', e);
      bankToast('⚠️ Bank gagal dimuat dari server. Cek koneksi & wb-config.js, lalu refresh.');
    }
    _isReady = true;
    _readyCbs.splice(0).forEach(cb=>{ try{ cb(); }catch(e){ console.error(e); } });
  }
  const _readyPromise = preload();

  // Trek lama dipangkas SEBELUM dikirim ke server (bukan di cache lokal),
  // biar payload gak numpuk sampai kena limit 100kb/bin punya akun gratis.
  // Status/streak tetap akurat karena itu angka tersendiri, bukan dihitung
  // dari panjang trekRows — trek yang dibuang cuma histori lama buat tampilan.
  const TREK_ROWS_CAP = 20;
  function trimForServer(list){
    if(!Array.isArray(list)) return list;
    return list.map(item=>{
      if(!item || !Array.isArray(item.trekRows) || item.trekRows.length<=TREK_ROWS_CAP) return item;
      return { ...item, trekRows: item.trekRows.slice(-TREK_ROWS_CAP) };
    });
  }

  function persist(data, appId){
    if(!_loadOk){
      bankToast(currentMemberId()==='guest' ? '⚠️ Login dulu untuk menyimpan ke Bank.' : '⚠️ Bank belum termuat dari server, simpan dibatalkan.');
      return false;
    }
    const app = appId || 'default';
    if(data===null) delete _mine[app];
    else _mine[app] = JSON.parse(JSON.stringify(data));
    const toSend = data===null ? null : trimForServer(data);
    _queue = _queue
      .then(()=>bankSet(toSend, app))
      .catch(e=>{
        console.error('[WB_BANK] simpan gagal:', e);
        const msg = (e.message||String(e));
        if(/100kb|413|too large/i.test(msg)) bankToast('⚠️ Bank kepenuhan (limit akun gratis 100kb). Hapus beberapa rumus lama lalu coba lagi.');
        else bankToast('⚠️ Gagal simpan bank ke server: '+msg);
      });
    return true;
  }

  global.WB_BANK = {
    currentId : currentMemberId,
    currentName: currentMemberName,
    get : (appId, memberId) => bankGet(appId, memberId),
    set : (data, appId, memberId) => bankSet(data, appId, memberId),
    add : (item, appId, memberId) => bankAdd(item, appId, memberId),
    clear : (appId, memberId) => bankClear(appId, memberId),
    listApps : (memberId) => bankListApps(memberId),
    countAll : (memberId) => bankCountAll(memberId),
    ready : _readyPromise,
    isReady : () => _isReady && _loadOk,
    onReady : (cb) => { if(_isReady) cb(); else _readyCbs.push(cb); },
    getSync : (appId) => JSON.parse(JSON.stringify(_mine[appId||'default'] || [])),
    setSync : (data, appId) => persist(data || [], appId),
    clearSync : (appId) => persist(null, appId),
    listAppsSync : () => Object.keys(_mine),
  };

  // ── Indikator member aktif di pojok kanan bawah (opsional, sekarang async) ─
  function showBankIndicator(){
    const mid = currentMemberId();
    if(mid==='guest') return;
    const div = document.createElement('div');
    div.id = 'wb-bank-indicator';
    div.style.cssText = [
      'position:fixed','bottom:10px','right:10px','z-index:9999',
      'background:rgba(22,29,53,.92)','border:1px solid #243154',
      'border-radius:8px','padding:5px 10px','font-size:11px',
      'color:#22e8ff','font-weight:700','pointer-events:none',
      'box-shadow:0 2px 8px rgba(0,0,0,.3)'
    ].join(';');
    div.textContent = '💾 Bank: ...';
    document.body.appendChild(div);
    function update(){
      if(!_isReady){ div.textContent = '💾 Bank: ...'; return; }
      if(!_loadOk){ div.textContent = '💾 Bank: (offline)'; return; }
      div.textContent = '💾 Bank: ' + Object.values(_mine).reduce((n,a)=>n+(a?a.length:0),0) + ' rumus';
    }
    update();
    setInterval(update, 2000);
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded', showBankIndicator);
  } else {
    showBankIndicator();
  }

})(window);
