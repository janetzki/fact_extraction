# Fact Extraction
Pattern learning and recognition using available DBpedia facts and the corresponding Wikipedia's free text.

## Setup
```shell
git clone https://github.com/jjanetzki/fact_extraction
sudo fact_extraction/setup/setup.sh
```

## Usage
### Syntactic Pattern Learning
```shell
fact_extraction/pattern_learning/learn_patterns.sh
```

### Type Pattern Learning
```shell
fact_extraction/type_learning/learn_types.sh
```

### The Fact Extraction itself
```shell
fact_extraction/pattern_recognition/extract_facts.sh
```

### Pattern Validation
If you want to test the fact extraction on ground truth data run:
```shell
fact_extraction/pattern_testing/test_patterns.sh
```
