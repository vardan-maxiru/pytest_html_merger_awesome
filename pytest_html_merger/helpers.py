from enum import Enum

class CaseStatuses(Enum):
    FAILED = 'Failed'
    PASSED = 'Passed'
    SKIPPED = 'Skipped'
    EXPECTED_FAILURES = 'Expected failures'
    UNEXPECTED_PASSES = 'Unexpected passes'

class CaseStatusData:
    
    @staticmethod
    def get_failed_data():
        return {
            "title": CaseStatuses.FAILED.value,
            "class_name": "failed"
        }
    
    @staticmethod
    def get_passed_data():
        return {
            "title": CaseStatuses.PASSED.value,
            "class_name": "passed"
        }
    
    @staticmethod
    def get_skipped_data():
        return {
            "title": CaseStatuses.SKIPPED.value,
            "class_name": "skipped"
        }
    
    @staticmethod
    def get_expected_faileres_data():
        return {
            "title": CaseStatuses.EXPECTED_FAILURES.value,
            "class_name": "expected-failures"
        }
    
    @staticmethod
    def get_unexpected_passes_data():
        return {
            "title": CaseStatuses.UNEXPECTED_PASSES.value,
            "class_name": "unexpected-passes"
        }