# Fact Extraction
Pattern learning and recognition using available DBpedia facts and the corresponding Wikipedia's free text.

## Setup
`$ cd setup/`

`$ ./setup.sh`

## Usage
### Syntactic Pattern Learning
`$ cd pattern_learning/`

`$ ./learn_patterns.sh`

### Type Pattern Learning
`$ cd type_learning/`

`$ ./learn_types.sh`

### The Fact Extraction itself
`$ cd pattern_recognition/`

`$ ./fact_extractor.sh`

### Pattern Validation
If you want to test the fact extraction on ground truth data run:

`$ cd pattern_testing/`

`$ ./test_patterns.sh`
