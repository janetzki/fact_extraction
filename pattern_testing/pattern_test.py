import imp

fact_extractor = imp.load_source('fact_extractor', '../pattern_recognition/fact_extractor.py')
from fact_extractor import FactExtractor

logger = imp.load_source('logger', '../logging/logger.py')
from logger import Logger

test_data = imp.load_source('test_data', '../pattern_testing/test_data.py')


def compare_facts(extracted_facts, reference_facts, logger):
    extracted_facts = set([(resource, rel, obj) for (resource, rel, obj, score, nl_sentence) in extracted_facts])
    reference_facts = set(reference_facts)
    equal = extracted_facts == reference_facts
    if equal:
        logger.print_pass('Facts are equal.')
    else:
        logger.print_fail(str(extracted_facts) + ' does not equal: ' + str(reference_facts))
    return equal


if __name__ == '__main__':
    fact_extractor = FactExtractor.from_config_file()
    logger = Logger.from_config_file()
    passed_tests = 0
    failed_tests = 0
    for test_case in test_data.test_articles_list():
        html = test_case[0]
        resource = test_case[1]
        expected_facts = test_case[2]
        extracted_facts = fact_extractor.extract_facts_from_html(html, resource)
        if compare_facts(extracted_facts, expected_facts, logger):
            passed_tests += 1
        else:
            failed_tests += 1
    print(str(passed_tests) + ' test cases passed, ' + str(failed_tests) + ' failed.')
