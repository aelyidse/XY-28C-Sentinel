import asyncio
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class TestResult:
    test_name: str
    status: str
    execution_time: float
    details: Dict
    timestamp: datetime

class TestAutomation:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_suite = []
        self.results = []
        
    def add_test(self, test_name: str, test_func: callable, params: Dict = None):
        """Register a test to be executed"""
        self.test_suite.append({
            'name': test_name,
            'func': test_func,
            'params': params or {}
        })
        
    async def run_tests(self) -> List[TestResult]:
        """Execute all registered tests"""
        self.results = []
        
        for test in self.test_suite:
            try:
                start_time = datetime.now()
                result = await self._execute_test(test)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                self.results.append(TestResult(
                    test_name=test['name'],
                    status='pass',
                    execution_time=execution_time,
                    details=result,
                    timestamp=datetime.now()
                ))
            except Exception as e:
                self.results.append(TestResult(
                    test_name=test['name'],
                    status='fail',
                    execution_time=0,
                    details={'error': str(e)},
                    timestamp=datetime.now()
                ))
                
        return self.results
        
    async def _execute_test(self, test: Dict):
        """Execute individual test"""
        try:
            result = await test['func'](**test['params'])
            return result
        except Exception as e:
            self.logger.error(f"Test {test['name']} failed: {str(e)}")
            raise
            
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        return {
            'summary': {
                'total_tests': len(self.results),
                'passed': sum(1 for r in self.results if r.status == 'pass'),
                'failed': sum(1 for r in self.results if r.status == 'fail'),
                'execution_time': sum(r.execution_time for r in self.results)
            },
            'details': [{
                'test_name': r.test_name,
                'status': r.status,
                'execution_time': r.execution_time,
                'timestamp': r.timestamp.isoformat(),
                'details': r.details
            } for r in self.results]
        }