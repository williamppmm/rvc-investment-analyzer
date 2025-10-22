#!/usr/bin/env python3
"""
Test rápido del endpoint de API de jubilación.
"""

import json
from app import app

# Crear cliente de prueba
client = app.test_client()

# Test del endpoint
def test_retirement_endpoint():
    print("Probando endpoint /api/calcular-inversion con retirement_plan...")

    payload = {
        "calculation_type": "retirement_plan",
        "current_age": 35,
        "retirement_age": 65,
        "initial_amount": 10000,
        "monthly_amount": 500,
        "scenario": "moderado",
        "annual_inflation": 0.03
    }

    response = client.post(
        '/api/calcular-inversion',
        data=json.dumps(payload),
        content_type='application/json'
    )

    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        data = json.loads(response.data)
        print("\nRespuesta exitosa:")
        print(f"- Tipo de cálculo: {data.get('calculation_type')}")

        result = data.get('result', {})
        if 'results' in result:
            res = result['results']
            print(f"\nResultados:")
            print(f"- Capital final: ${res.get('final_capital'):,.2f}")
            print(f"- Capital inicial: ${res.get('initial_capital'):,.2f}")
            print(f"- Aportaciones: ${res.get('total_contributions'):,.2f}")
            print(f"- Intereses: ${res.get('total_interest'):,.2f}")

        if 'scenarios' in result:
            print(f"\nEscenarios:")
            for name, scenario in result['scenarios'].items():
                print(f"- {name}: ${scenario['final_value']:,.2f}")

        if 'milestones' in result:
            print(f"\nHitos ({len(result['milestones'])}):")
            for m in result['milestones'][:3]:  # Mostrar primeros 3
                print(f"- {m['label']}: Año {m['year']} (edad {m['age']})")

        print("\n✓ Test PASSED")
        return True
    else:
        print(f"\n✗ Error: {response.data.decode()}")
        return False


if __name__ == "__main__":
    with app.app_context():
        success = test_retirement_endpoint()
        exit(0 if success else 1)
