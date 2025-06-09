import os
from loguru import logger # type: ignore
from etl import extract_data, save_output

# Updated load_config with environment variable support
def load_config():
    return {
        "input_directory": os.getenv("INPUT_DIR", "/data/input"),
        "output_directory": os.getenv("OUTPUT_DIR", "/data/output")
    }

if __name__ == "__main__":
    config = load_config()
    input_dir = config['input_directory']
    output_dir = config['output_directory']

    os.makedirs(output_dir, exist_ok=True)

    try:
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    except FileNotFoundError:
        logger.error(f"Input directory '{input_dir}' not found.")
        exit(1)

    for file_name in files:
        file_path = os.path.join(input_dir, file_name)
        logger.info(f"Processing: {file_path}")

        try:
            content = extract_data(file_path)
            if content:
                output_file = os.path.splitext(file_name)[0] + ".txt"
                save_output(os.path.join(output_dir, output_file), content)
        except Exception as e:
            logger.error(f"Failed to process {file_name}: {e}")
