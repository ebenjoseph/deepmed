DATA_DIR = data
RAW_DATA_DIR = $(DATA_DIR)/raw
BUILD_DATA_DIR = $(DATA_DIR)/build
S3_BUCKET = deepmed-data

AWS = aws
COCHRANE_NORMALIZE = ./bin/cochranenormalize

.PHONY: all

all: $(BUILD_DATA_DIR)/cochrane_assessments_normalized.jsonl

$(RAW_DATA_DIR)/%:
	$(AWS) s3 cp s3://$(S3_BUCKET)/$* $@

$(BUILD_DATA_DIR)/cochrane_assessments_normalized.jsonl: $(RAW_DATA_DIR)/cochrane_assessments.jsonl $(COCHRANE_NORMALIZE) $(BUILD_DATA_DIR)
	$(COCHRANE_NORMALIZE) $< > $@

$(BUILD_DATA_DIR):
	mkdir -p $@