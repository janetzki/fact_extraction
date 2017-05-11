from pattern_recognition import FactExtractor
from logger import Logger
import test_data


def compare_facts(extracted_facts, reference_facts, logger):
    extracted_facts = set([(resource, rel, obj) for (resource, rel, obj, score, nl_sentence) in extracted_facts])
    reference_facts = set(reference_facts)
    equal = extracted_facts == reference_facts
    if equal:
        logger.print_pass('Facts are equal.')
    else:
        logger.print_fail(str(extracted_facts) + ' does not equal: ' + str(reference_facts))
        if len(extracted_facts) > len(reference_facts):
            logger.print_aligned('Contains false positives')
        elif len(extracted_facts) < len(reference_facts):
            logger.print_aligned('Contains false negatives')
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
