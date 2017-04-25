FROM python:2.7.10
RUN apt-get update
RUN useradd -ms /bin/bash textext
WORKDIR /home/textext
RUN git clone https://github.com/jjanetzki/fact_extraction.git
WORKDIR /home/textext/fact_extraction

# Setup
RUN cd setup
RUN ./setup.sh
RUN cd ..

# Pattern Learning
RUN cd pattern_learning/
RUN ./learn_patterns.sh
RUN cd ..

# Type Pattern Learning
RUN cd type_learning/
RUN ./learn_types.sh
RUN cd ..

# The Fact Extraction itself
RUN cd pattern_recognition/
RUN ./fact_extractor.sh
RUN cd ..

# Pattern Validation
# RUN cd pattern_testing/
# RUN ./test_patterns.sh
# RUN cd ..