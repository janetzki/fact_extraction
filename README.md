# Fact Extraction
Pattern learning and recognition using available DBpedia facts and the corresponding Wikipedia's free text.

## Setup
```shell
git clone https://github.com/jjanetzki/fact_extraction
sudo fact_extraction/setup/setup.sh
```
This will download and setup all required data sources. It may take several hours depending on your internet connection. 

## Usage
### Syntactic Pattern Learning
```shell
sudo fact_extraction/pattern_learning/learn_patterns.sh
```

### Type Pattern Learning
```shell
sudo fact_extraction/type_learning/learn_types.sh
```

### The Fact Extraction itself
```shell
sudo fact_extraction/pattern_recognition/extract_facts.sh
```

### Pattern Validation
If you want to test the fact extraction on ground truth data run:
```shell
sudo fact_extraction/pattern_testing/test_patterns.sh
```
