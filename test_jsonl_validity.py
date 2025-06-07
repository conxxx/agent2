import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JSONL_FILE = 'products_vertex_ai.jsonl'
EXPECTED_KEYS = ['id', 'title', 'description', 'categories', 'priceInfo', 'availability', 'attributes']

def validate_jsonl_file(filepath):
    logger.info(f"Starting validation for {filepath}...")
    line_count = 0
    valid_json_count = 0
    invalid_json_lines = []
    missing_keys_issues = []

    try:
        with open(filepath, 'r') as f:
            for i, line in enumerate(f):
                line_count += 1
                try:
                    data = json.loads(line.strip())
                    valid_json_count += 1
                    
                    # Check for expected top-level keys
                    current_missing_keys = []
                    for key in EXPECTED_KEYS:
                        if key not in data:
                            current_missing_keys.append(key)
                    if current_missing_keys:
                        missing_keys_issues.append({
                            "line_number": line_count,
                            "id": data.get("id", "N/A"),
                            "missing_keys": current_missing_keys
                        })

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON on line {line_count}: {e}")
                    invalid_json_lines.append(line_count)
        
        logger.info(f"Finished processing {filepath}.")
        logger.info(f"Total lines processed: {line_count}")
        logger.info(f"Valid JSON objects: {valid_json_count}")

        if invalid_json_lines:
            logger.error(f"Lines with invalid JSON: {invalid_json_lines}")
        else:
            logger.info("All lines are valid JSON.")

        if missing_keys_issues:
            logger.warning("Some objects are missing expected top-level keys:")
            for issue in missing_keys_issues:
                logger.warning(f"  Line {issue['line_number']} (ID: {issue['id']}): Missing {', '.join(issue['missing_keys'])}")
        elif line_count > 0:
            logger.info("All valid JSON objects contain the expected top-level keys.")
            
        if line_count == 0:
            logger.warning("The file is empty.")
            return False
        
        return not invalid_json_lines and not missing_keys_issues

    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False

if __name__ == '__main__':
    is_valid = validate_jsonl_file(JSONL_FILE)
    if is_valid:
        logger.info(f"'{JSONL_FILE}' appears to be valid and well-formed for basic checks.")
    else:
        logger.error(f"'{JSONL_FILE}' has issues. Please check logs above.")
