#!/usr/bin/env python3
"""
Test unitarios para el endpoint /api/top-opportunities
"""

import unittest
import json
import sys
import os

# Añadir el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

class TestTopOpportunitiesEndpoint(unittest.TestCase):
    """Tests para el endpoint /api/top-opportunities"""
    
    def setUp(self):
        """Configurar el cliente de test"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_endpoint_basic_functionality(self):
        """Test básico del endpoint sin parámetros"""
        response = self.app.get('/api/top-opportunities')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('opportunities', data['data'])
        self.assertIn('metadata', data['data'])
        
        # Verificar que hay datos
        opportunities = data['data']['opportunities']
        self.assertIsInstance(opportunities, list)
        self.assertGreater(len(opportunities), 0)
    
    def test_filtering_by_min_score(self):
        """Test filtrado por score mínimo"""
        response = self.app.get('/api/top-opportunities?min_score=75')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        opportunities = data['data']['opportunities']
        
        # Todos los resultados deben tener score >= 75
        for opportunity in opportunities:
            self.assertGreaterEqual(opportunity['rvc_score'], 75.0)
    
    def test_sorting_functionality(self):
        """Test funcionalidad de ordenamiento"""
        # Test ordenamiento por RVC score (default)
        response = self.app.get('/api/top-opportunities?sort_by=rvc_score')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        opportunities = data['data']['opportunities']
        
        if len(opportunities) > 1:
            for i in range(1, len(opportunities)):
                current_score = opportunities[i]['rvc_score'] or 0
                previous_score = opportunities[i-1]['rvc_score'] or 0
                self.assertLessEqual(current_score, previous_score)
    
    def test_limit_parameter(self):
        """Test parámetro de límite"""
        limit = 5
        response = self.app.get(f'/api/top-opportunities?limit={limit}')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        opportunities = data['data']['opportunities']
        
        self.assertLessEqual(len(opportunities), limit)
    
    def test_sector_filtering(self):
        """Test filtrado por sector"""
        response = self.app.get('/api/top-opportunities?sector=technology')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        opportunities = data['data']['opportunities']
        
        # Todos los resultados deben ser del sector technology
        for opportunity in opportunities:
            sector = (opportunity.get('sector') or '').lower()
            self.assertIn('technology', sector)
    
    def test_metadata_structure(self):
        """Test estructura de metadatos"""
        response = self.app.get('/api/top-opportunities')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        metadata = data['data']['metadata']
        
        # Verificar campos requeridos en metadata
        required_fields = [
            'total_count', 'average_score', 'sectors_available',
            'filters_applied', 'generated_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, metadata)
        
        # Verificar tipos
        self.assertIsInstance(metadata['total_count'], int)
        self.assertIsInstance(metadata['average_score'], (int, float))
        self.assertIsInstance(metadata['sectors_available'], list)
        self.assertIsInstance(metadata['filters_applied'], dict)
    
    def test_opportunity_structure(self):
        """Test estructura de cada oportunidad"""
        response = self.app.get('/api/top-opportunities?limit=1')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        opportunities = data['data']['opportunities']
        
        if opportunities:
            opportunity = opportunities[0]
            
            # Campos requeridos
            required_fields = [
                'ticker', 'company_name', 'rvc_score', 'classification',
                'sector', 'last_updated'
            ]
            
            for field in required_fields:
                self.assertIn(field, opportunity)
            
            # Verificar tipos
            self.assertIsInstance(opportunity['ticker'], str)
            self.assertIsInstance(opportunity['rvc_score'], (int, float))
            self.assertGreater(opportunity['rvc_score'], 0)
    
    def test_invalid_parameters(self):
        """Test parámetros inválidos"""
        # Test score mínimo inválido
        response = self.app.get('/api/top-opportunities?min_score=invalid')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_top_opportunity_is_schw(self):
        """Test que la mejor oportunidad es SCHW (basado en datos actuales)"""
        response = self.app.get('/api/top-opportunities?limit=1')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        opportunities = data['data']['opportunities']
        
        if opportunities:
            top_opportunity = opportunities[0]
            self.assertEqual(top_opportunity['ticker'], 'SCHW')
            self.assertGreater(top_opportunity['rvc_score'], 75.0)

if __name__ == '__main__':
    print("🧪 Ejecutando tests para /api/top-opportunities...")
    unittest.main(verbosity=2)