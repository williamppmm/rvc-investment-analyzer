#!/usr/bin/env python3
"""
Tests para la calculadora de plan de jubilación.
"""

from investment_calculator import InvestmentCalculator


def test_retirement_plan_basic():
    """Test básico del plan de jubilación."""
    calc = InvestmentCalculator()

    result = calc.calculate_retirement_plan(
        current_age=35,
        retirement_age=65,
        initial_amount=10000,
        monthly_contribution=500,
        annual_return=0.07,
        annual_inflation=0.03,
        include_yearly_detail=True
    )

    # Verificar estructura de respuesta
    assert "input" in result
    assert "results" in result
    assert "scenarios" in result
    assert "yearly_projections" in result
    assert "milestones" in result
    assert "composition" in result

    # Verificar inputs
    assert result["input"]["current_age"] == 35
    assert result["input"]["retirement_age"] == 65
    assert result["input"]["years_to_retirement"] == 30

    # Verificar que hay resultados
    assert result["results"]["final_capital"] > 0
    assert result["results"]["total_contributions"] > 0
    assert result["results"]["total_interest"] > 0

    # Verificar que final_capital = initial + contributions + interest
    total = (
        result["results"]["initial_capital"] +
        result["results"]["total_contributions"] +
        result["results"]["total_interest"]
    )
    assert abs(total - result["results"]["final_capital"]) < 1.0  # Permitir pequeño error de redondeo

    # Verificar escenarios
    assert "conservador" in result["scenarios"]
    assert "realista" in result["scenarios"]
    assert "optimista" in result["scenarios"]

    # Verificar que optimista > realista > conservador
    assert result["scenarios"]["optimista"]["final_value"] > result["scenarios"]["realista"]["final_value"]
    assert result["scenarios"]["realista"]["final_value"] > result["scenarios"]["conservador"]["final_value"]

    # Verificar proyecciones anuales
    assert len(result["yearly_projections"]) <= 30

    # Verificar que el último año coincide con el resultado final
    last_year = result["yearly_projections"][-1]
    assert abs(last_year["portfolio_value"] - result["results"]["final_capital"]) < 1.0

    # Verificar composición suma 100%
    composition_total = (
        result["composition"]["initial_pct"] +
        result["composition"]["contributions_pct"] +
        result["composition"]["interest_pct"]
    )
    assert abs(composition_total - 100.0) < 0.1

    print("✅ Test básico del plan de jubilación: PASSED")


def test_retirement_plan_inflation_adjustment():
    """Test que verifica el ajuste por inflación."""
    calc = InvestmentCalculator()

    result = calc.calculate_retirement_plan(
        current_age=30,
        retirement_age=40,  # 10 años
        initial_amount=0,
        monthly_contribution=1000,
        annual_return=0.07,
        annual_inflation=0.03,
        include_yearly_detail=True
    )

    # Verificar que las aportaciones aumentan con la inflación
    yearly_projections = result["yearly_projections"]

    # Año 1: aportación base
    year1_contribution = yearly_projections[0]["annual_contribution"]

    # Año 10: debería ser mayor por inflación
    year10_contribution = yearly_projections[9]["annual_contribution"]

    # Calcular inflación esperada: (1.03)^9 ≈ 1.3048
    expected_factor = (1.03 ** 9)
    expected_year10 = year1_contribution * expected_factor

    # Verificar que la aportación del año 10 es aproximadamente correcta
    assert abs(year10_contribution - expected_year10) < 100  # Margen de error

    print("✅ Test de ajuste por inflación: PASSED")


def test_retirement_plan_validations():
    """Test de validaciones."""
    calc = InvestmentCalculator()

    # Test edad actual fuera de rango
    try:
        calc.calculate_retirement_plan(
            current_age=17,  # Menor a 18
            retirement_age=65,
            initial_amount=10000,
            monthly_contribution=500,
            annual_return=0.07,
            annual_inflation=0.03
        )
        assert False, "Debería haber lanzado ValueError"
    except ValueError as e:
        assert "Edad actual debe estar entre 18 y 75" in str(e)

    # Test edad de jubilación inválida
    try:
        calc.calculate_retirement_plan(
            current_age=65,
            retirement_age=60,  # Menor a edad actual
            initial_amount=10000,
            monthly_contribution=500,
            annual_return=0.07,
            annual_inflation=0.03
        )
        assert False, "Debería haber lanzado ValueError"
    except ValueError as e:
        assert "mayor a la edad actual" in str(e)

    # Test rendimiento fuera de rango
    try:
        calc.calculate_retirement_plan(
            current_age=35,
            retirement_age=65,
            initial_amount=10000,
            monthly_contribution=500,
            annual_return=0.25,  # 25% - fuera de rango
            annual_inflation=0.03
        )
        assert False, "Debería haber lanzado ValueError"
    except ValueError as e:
        assert "Rendimiento anual debe estar entre -10% y +20%" in str(e)

    print("✅ Test de validaciones: PASSED")


def test_retirement_plan_milestones():
    """Test de detección de hitos."""
    calc = InvestmentCalculator()

    result = calc.calculate_retirement_plan(
        current_age=25,
        retirement_age=65,
        initial_amount=50000,
        monthly_contribution=1000,
        annual_return=0.08,
        annual_inflation=0.03,
        include_yearly_detail=True
    )

    milestones = result["milestones"]

    # Con estos parámetros, deberíamos alcanzar varios hitos
    assert len(milestones) > 0

    # Verificar que los hitos están en orden
    for i in range(len(milestones) - 1):
        assert milestones[i]["amount"] < milestones[i + 1]["amount"]
        assert milestones[i]["year"] <= milestones[i + 1]["year"]

    # Verificar que cada hito tiene los campos correctos
    for milestone in milestones:
        assert "amount" in milestone
        assert "year" in milestone
        assert "age" in milestone
        assert "label" in milestone
        assert milestone["age"] >= 25
        assert milestone["age"] <= 65

    print("✅ Test de hitos: PASSED")


def test_retirement_plan_no_inflation():
    """Test con inflación cero."""
    calc = InvestmentCalculator()

    result = calc.calculate_retirement_plan(
        current_age=40,
        retirement_age=50,
        initial_amount=0,
        monthly_contribution=1000,
        annual_return=0.06,
        annual_inflation=0.0,  # Sin inflación
        include_yearly_detail=True
    )

    # Con inflación cero, todas las aportaciones anuales deberían ser iguales
    yearly_projections = result["yearly_projections"]

    expected_annual = 1000 * 12  # $12,000

    for year_data in yearly_projections:
        # Permitir pequeño margen de error por redondeo
        assert abs(year_data["annual_contribution"] - expected_annual) < 1.0

    print("✅ Test sin inflación: PASSED")


def test_retirement_plan_scenarios_difference():
    """Test que verifica diferencia correcta entre escenarios."""
    calc = InvestmentCalculator()

    result = calc.calculate_retirement_plan(
        current_age=30,
        retirement_age=60,
        initial_amount=20000,
        monthly_contribution=800,
        annual_return=0.08,  # 8%
        annual_inflation=0.03,
        include_yearly_detail=False
    )

    scenarios = result["scenarios"]

    # Los escenarios deberían usar 6%, 8%, y 10% respectivamente
    # Verificar que hay diferencias significativas
    conservador = scenarios["conservador"]["final_value"]
    realista = scenarios["realista"]["final_value"]
    optimista = scenarios["optimista"]["final_value"]

    # La diferencia entre escenarios debería ser al menos 5%
    diff_cons_real = (realista - conservador) / conservador
    diff_real_opt = (optimista - realista) / realista

    assert diff_cons_real > 0.05  # Al menos 5% de diferencia
    assert diff_real_opt > 0.05

    print("✅ Test de diferencias entre escenarios: PASSED")


if __name__ == "__main__":
    print("Ejecutando tests del plan de jubilación...\n")

    test_retirement_plan_basic()
    test_retirement_plan_inflation_adjustment()
    test_retirement_plan_validations()
    test_retirement_plan_milestones()
    test_retirement_plan_no_inflation()
    test_retirement_plan_scenarios_difference()

    print("\n" + "=" * 50)
    print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("=" * 50)
