"""Static app wiring checks without needing Streamlit installed."""
import ast
import inspect
import unittest
from pathlib import Path
from model_v05 import simulate
from investment_model import project_cashflows, debt_schedule

class TestAppContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Path(__file__).with_name('app.py').read_text(encoding='utf-8')
        cls.tree=ast.parse(cls.source)
    def test_simulate_kwargs_match_signature(self):
        valid=set(inspect.signature(simulate).parameters)
        for node in ast.walk(self.tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='simulate':
                self.assertTrue({kw.arg for kw in node.keywords if kw.arg}.issubset(valid))
    def test_investment_kwargs_match_signature(self):
        for func in (project_cashflows,debt_schedule):
            valid=set(inspect.signature(func).parameters)
            for node in ast.walk(self.tree):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id==func.__name__:
                    self.assertTrue({kw.arg for kw in node.keywords if kw.arg}.issubset(valid))
    def test_all_required_modules_imported(self):
        imports={n.module for n in ast.walk(self.tree) if isinstance(n,ast.ImportFrom)}
        self.assertTrue({'benchmark_data','model_v05','investment_model'}.issubset(imports))
    def test_app_sections_present(self):
        for heading in ('초기 투자', '사업 전체', '자기자본','할인 PBP','누적 현금흐름'):
            self.assertIn(heading,self.source)

if __name__=='__main__':unittest.main()
