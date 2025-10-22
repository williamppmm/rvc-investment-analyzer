"""
Adaptive RVC calculator handling partial data availability.
"""

from __future__ import annotations

from typing import Dict, List, Optional


class RVCCalculator:
    """Compute RVC scores given a metrics dictionary."""

    def __init__(self):
        self.weights = {
            "valoracion": 0.40,
            "calidad": 0.35,
            "salud": 0.15,
            "crecimiento": 0.10,
        }

    @staticmethod
    def _pick_metric(metrics: Dict, keys: List[str], default: Optional[float] = None) -> Optional[float]:
        """Return first non-None metric value using the provided priority."""
        for key in keys:
            value = metrics.get(key)
            if value is not None:
                return value
        return default

    def calculate_score(self, metrics: Dict) -> Dict:
        valuation = self._valuation(metrics)
        quality = self._quality(metrics)
        health = self._health(metrics)
        growth = self._growth(metrics)

        breakdown = {
            "valoracion": valuation,
            "calidad": quality,
            "salud": health,
            "crecimiento": growth,
        }

        weights = self._adjust_weights(breakdown)
        total = 0.0
        for key, data in breakdown.items():
            score = data["score"]
            if score is not None:
                total += score * weights[key]

        classification = self._classify(total)
        recommendation = self._recommend(total, breakdown, metrics.get("data_completeness", 0))

        return {
            "total_score": round(total, 2),
            "classification": classification,
            "recommendation": recommendation,
            "breakdown": breakdown,
            "data_completeness": metrics.get("data_completeness", 0),
            "confidence_level": self._confidence(metrics),
        }

    def _valuation(self, metrics: Dict) -> Dict:
        components = []
        used: List[str] = []

        pe = metrics.get("pe_ratio")
        if pe is not None and pe > 0:
            if pe < 15:
                score = 100
            elif pe < 20:
                score = 85
            elif pe < 25:
                score = 65
            elif pe < 30:
                score = 45
            else:
                score = 20
            components.append(("P/E", score, 0.4))
            used.append(f"P/E: {pe:.2f}")

        peg = metrics.get("peg_ratio")
        if peg is not None and peg > 0:
            if peg < 1:
                score = 100
            elif peg < 1.25:
                score = 85
            elif peg < 1.75:
                score = 55
            elif peg < 2.5:
                score = 35
            else:
                score = 15
            components.append(("PEG", score, 0.35))
            used.append(f"PEG: {peg:.2f}")

        pb = metrics.get("price_to_book")
        if pb is not None and pb > 0:
            if pb < 1:
                score = 100
            elif pb < 3:
                score = 75
            elif pb < 5:
                score = 45
            else:
                score = 20
            components.append(("P/B", score, 0.25))
            used.append(f"P/B: {pb:.2f}")

        result = self._weighted_result(components, used, "Sin datos de valoracion")
        has_pe = any(name == "P/E" for name, _, _ in components)
        if not has_pe and result["score"] < 30 and any("P/B" in item or "PEG" in item for item in used):
            result["score"] = 30.0
        if not has_pe and result["score"] < 30 and any("P/B" in item or "PEG" in item for item in used):
            result["score"] = 30.0
        if pe is not None and pe >= 50:
            used.append("Nota: P/E elevado, riesgo de sobrevaloracion.")
        return result

    def _quality(self, metrics: Dict) -> Dict:
        components = []
        used: List[str] = []

        roe = metrics.get("roe")
        if roe is not None:
            if roe > 25:
                score = 100
            elif roe > 20:
                score = 85
            elif roe > 15:
                score = 70
            elif roe > 10:
                score = 50
            elif roe > 5:
                score = 30
            else:
                score = 10
            components.append(("ROE", score, 0.4))
            used.append(f"ROE: {roe:.1f}%")

        roic = metrics.get("roic")
        if roic is not None:
            if roic > 20:
                score = 100
            elif roic > 15:
                score = 85
            elif roic > 10:
                score = 65
            elif roic > 8:
                score = 45
            else:
                score = 20
            components.append(("ROIC", score, 0.35))
            used.append(f"ROIC: {roic:.1f}%")

        op_margin = metrics.get("operating_margin")
        if op_margin is not None:
            if op_margin > 25:
                score = 100
            elif op_margin > 20:
                score = 80
            elif op_margin > 15:
                score = 60
            elif op_margin > 10:
                score = 40
            else:
                score = 20
            components.append(("Operating Margin", score, 0.25))
            used.append(f"Op. Margin: {op_margin:.1f}%")

        net_margin = metrics.get("net_margin")
        if net_margin is not None:
            if net_margin > 25:
                score = 100
            elif net_margin > 20:
                score = 80
            elif net_margin > 15:
                score = 60
            elif net_margin > 10:
                score = 40
            else:
                score = 20
            components.append(("Net Margin", score, 0.15))
            used.append(f"Net Margin: {net_margin:.1f}%")

        result = self._weighted_result(components, used, "Sin datos de calidad")
        revenue_growth = self._pick_metric(
            metrics,
            ["revenue_growth_5y", "revenue_growth", "revenue_growth_qoq"],
            default=0.0,
        )
        earnings_growth = self._pick_metric(
            metrics,
            [
                "earnings_growth_this_y",
                "earnings_growth_next_y",
                "earnings_growth_next_5y",
                "earnings_growth_qoq",
                "earnings_growth",
            ],
            default=0.0,
        )
        if result["score"] < 40 and revenue_growth >= 25 and earnings_growth >= 10:
            result["score"] = min(result["score"] + 10, 55)
            result["metrics_used"].append("Bonus: reinversion agresiva respalda crecimiento (>25% ingresos).")
        return result

    def _health(self, metrics: Dict) -> Dict:
        components = []
        used: List[str] = []

        debt = metrics.get("debt_to_equity")
        if debt is not None:
            if debt < 0.5:
                score = 100
            elif debt < 1:
                score = 80
            elif debt < 1.5:
                score = 55
            elif debt < 2:
                score = 35
            else:
                score = 15
            components.append(("Debt/Equity", score, 0.6))
            used.append(f"D/E: {debt:.2f}")

        current = metrics.get("current_ratio")
        if current is not None:
            if current > 2:
                score = 100
            elif current > 1.5:
                score = 80
            elif current > 1:
                score = 60
            elif current > 0.7:
                score = 40
            else:
                score = 20
            components.append(("Current Ratio", score, 0.3))
            used.append(f"Current: {current:.2f}")

        quick = metrics.get("quick_ratio")
        if quick is not None:
            if quick > 1.5:
                score = 100
            elif quick > 1.2:
                score = 80
            elif quick > 1:
                score = 60
            elif quick > 0.7:
                score = 40
            else:
                score = 20
            components.append(("Quick Ratio", score, 0.1))
            used.append(f"Quick: {quick:.2f}")

        return self._weighted_result(components, used, "Sin datos de salud financiera")

    def _growth(self, metrics: Dict) -> Dict:
        components = []
        used: List[str] = []

        revenue_growth = self._pick_metric(
            metrics,
            ["revenue_growth_5y", "revenue_growth", "revenue_growth_qoq"],
        )
        if revenue_growth is not None:
            if revenue_growth > 25:
                score = 100
            elif revenue_growth > 20:
                score = 85
            elif revenue_growth > 15:
                score = 65
            elif revenue_growth > 10:
                score = 45
            elif revenue_growth > 5:
                score = 30
            else:
                score = 15
            components.append(("Revenue Growth", score, 0.6))
            used.append(f"Rev. Growth: {revenue_growth:.1f}%")

        earnings_growth = self._pick_metric(
            metrics,
            [
                "earnings_growth_this_y",
                "earnings_growth_next_y",
                "earnings_growth_next_5y",
                "earnings_growth_qoq",
                "earnings_growth",
            ],
        )
        if earnings_growth is not None:
            if earnings_growth > 25:
                score = 100
            elif earnings_growth > 15:
                score = 80
            elif earnings_growth > 5:
                score = 55
            elif earnings_growth > 0:
                score = 35
            else:
                score = 15
            components.append(("Earnings Growth", score, 0.4))
            used.append(f"Earn. Growth: {earnings_growth:.1f}%")

        return self._weighted_result(components, used, "Sin datos de crecimiento")

    def _weighted_result(self, components: List[tuple], used: List[str], fallback: str) -> Dict:
        active = [(score, weight) for _, score, weight in components]
        if active:
            total_weight = sum(weight for _, _, weight in components if weight)
            if total_weight == 0:
                average = sum(score for score, _ in active) / len(active)
            else:
                average = sum(score * weight for score, weight in active) / total_weight
            return {"score": round(average, 2), "metrics_used": used}
        return {"score": 50.0, "metrics_used": [fallback]}

    def _adjust_weights(self, breakdown: Dict) -> Dict:
        valid = [k for k, v in breakdown.items() if v["score"] is not None and v["metrics_used"]]
        if len(valid) == len(self.weights):
            return self.weights
        total = sum(self.weights[k] for k in valid) or 1.0
        return {k: (self.weights[k] / total if k in valid else 0.0) for k in self.weights}

    def _classify(self, score: float) -> str:
        if score >= 70:
            return "🟢 Razonable o mejor"
        if score >= 50:
            return "🟡 Intermedio / Observar"
        return "🔴 Exigente / Sobrevalorada"

    def _recommend(self, score: float, breakdown: Dict, completeness: float) -> str:
        prefix = "⚠️ Analisis con datos limitados. " if completeness < 50 else ""
        extra: List[str] = []
        valuation_score = breakdown["valoracion"]["score"]
        quality_score = breakdown["calidad"]["score"]
        health_score = breakdown["salud"]["score"]
        growth_score = breakdown["crecimiento"]["score"]

        if valuation_score < 35:
            extra.append("Precio exige expectativas muy altas.")
        if quality_score < 40:
            extra.append("Rentabilidad comprimida por fase de inversion.")
        if growth_score > 70:
            extra.append("Crecimiento operativo se mantiene dinamico.")
        if health_score > 80:
            extra.append("Balance y liquidez son solidos.")

        if score >= 70:
            strengths = [self._label_dimension(dim) for dim, data in breakdown.items() if data["score"] > 70]
            msg = f"{prefix}Equilibrio atractivo: destaca en {', '.join(strengths)}." if strengths else f"{prefix}Valoracion razonable con fundamentos solidos."
            if extra:
                msg += " " + " ".join(extra)
            return msg
        if score >= 50:
            watch = [self._label_dimension(dim) for dim, data in breakdown.items() if data["score"] < 60]
            msg = f"{prefix}Mantener/observar." 
            if watch:
                msg += f" Vigilar {', '.join(watch)}."
            if extra:
                msg += " " + " ".join(extra)
            return msg
        weaknesses = [self._label_dimension(dim) for dim, data in breakdown.items() if data["score"] < 50]
        msg = f"{prefix}Riesgo elevado."
        if weaknesses:
            msg += f" Presion en {', '.join(weaknesses)}."
        if extra:
            msg += " " + " ".join(extra)
        return msg

    def _confidence(self, metrics: Dict) -> str:
        completeness = metrics.get("data_completeness", 0)
        critical = [
            metrics.get("pe_ratio"),
            metrics.get("roe"),
            metrics.get("operating_margin"),
        ]
        if metrics.get("primary_source") == "fallback_example" or any(value is None for value in critical):
            return "Media" if completeness >= 80 else "Baja"
        if completeness >= 80:
            return "Alta"
        if completeness >= 60:
            return "Media"
        if completeness >= 40:
            return "Baja"
        return "Muy Baja"

    def _label_dimension(self, dim_key: str) -> str:
        mapping = {
            "valoracion": "valoracion",
            "calidad": "calidad del negocio",
            "salud": "salud financiera",
            "crecimiento": "crecimiento",
        }
        return mapping.get(dim_key, dim_key)
