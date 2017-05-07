# Fact Extraction
Pattern learning and recognition using available DBpedia facts and the corresponding Wikipedia's free text.

## Setup
`$ git clone https://github.com/jjanetzki/fact_extraction`
`$ sudo fact_extraction/setup/setup.sh`

## Usage
### Syntactic Pattern Learning
`$ fact_extraction/pattern_learning/learn_patterns.sh`

### Type Pattern Learning
`$ fact_extraction/type_learning/learn_types.sh`

### The Fact Extraction itself
`$ fact_extraction/pattern_recognition/fact_extractor.sh`

### Pattern Validation
If you want to test the fact extraction on ground truth data run:

`$ fact_extraction/pattern_testing/test_patterns.sh`
