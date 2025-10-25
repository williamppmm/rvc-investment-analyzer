(function(){
  const STORAGE_KEY = 'rvc_currency';
  const RATE_KEY = 'rvc_rates_v1';
  const DEFAULT_CURRENCY = 'USD';
  const SYMBOLS = { USD: 'US$', EUR: '€' };
  const rates = {}; // base USD -> target
  const lastFetchedMap = {}; // per target currency
  let current = localStorage.getItem(STORAGE_KEY) || DEFAULT_CURRENCY;

  // Cargar tasas persistidas (si existen)
  try {
    const raw = localStorage.getItem(RATE_KEY);
    if (raw) {
      const saved = JSON.parse(raw);
      Object.keys(saved || {}).forEach(k => {
        const entry = saved[k];
        if (entry && typeof entry.rate === 'number') {
          rates[k] = entry.rate;
          lastFetchedMap[k] = Number(entry.ts) || 0;
        }
      });
    }
  } catch (_) { /* ignore */ }

  async function ensureRate(target){
    target = (target || 'EUR').toUpperCase();
    if(target === 'USD') return 1;
    const now = Date.now();
    const last = lastFetchedMap[target] || 0;
    if(rates[target] && (now - last) < 6*60*60*1000){
      return rates[target];
    }
    try {
      const res = await fetch(`/api/exchange-rate?base=USD&target=${encodeURIComponent(target)}`);
      if(res.ok){
        const data = await res.json();
        if(data && typeof data.rate === 'number'){
          rates[target] = data.rate;
          lastFetchedMap[target] = now;
          // Persistir mapa de tasas
          try {
            const existing = JSON.parse(localStorage.getItem(RATE_KEY) || '{}');
            existing[target] = { rate: rates[target], ts: now };
            localStorage.setItem(RATE_KEY, JSON.stringify(existing));
          } catch (_) { /* ignore */ }
          return rates[target];
        }
      }
    } catch (e) {
      // ignore; fallback to previous rate if any
    }
    return rates[target] || 1;
  }

  function setCurrency(code){
    current = (code || DEFAULT_CURRENCY).toUpperCase();
    localStorage.setItem(STORAGE_KEY, current);
  }

  function getCurrency(){
    return current;
  }

  function getSymbol(){
    return SYMBOLS[current] || current;
  }

  function convertFromUSD(amount){
    if(current === 'USD') return Number(amount) || 0;
    const rate = rates[current];
    if(typeof rate !== 'number') return Number(amount) || 0;
    return (Number(amount) || 0) * rate;
  }

  window.CurrencyManager = { ensureRate, setCurrency, getCurrency, getSymbol, convertFromUSD };
})();
