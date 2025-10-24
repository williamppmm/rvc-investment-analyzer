-- SQL de ejemplo para consultar la caché local de RVC (SQLite)

-- 1) Últimos tickers analizados
SELECT ticker, last_updated
FROM financial_cache
ORDER BY datetime(last_updated) DESC
LIMIT 20;

-- 2) Top 20 por score (RVC)
SELECT ticker, score, classification, last_calculated
FROM rvc_scores
ORDER BY score DESC
LIMIT 20;

-- 3) Ver P/E guardado para un ticker
SELECT json_extract(data, '$.pe_ratio') AS pe_ratio, last_updated
FROM financial_cache
WHERE ticker = 'AAPL'
ORDER BY datetime(last_updated) DESC
LIMIT 1;

-- 4) Conteo de registros por día (actividad)
SELECT strftime('%Y-%m-%d', last_updated) AS day, COUNT(*) AS n
FROM financial_cache
GROUP BY day
ORDER BY day DESC
LIMIT 14;

-- 5) Detectar registros antiguos (posibles a refrescar)
SELECT ticker, last_updated
FROM financial_cache
WHERE datetime(last_updated) < datetime('now', '-7 days')
ORDER BY last_updated ASC
LIMIT 50;
