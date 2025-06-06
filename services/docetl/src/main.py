import os
from etl import load_config, extract_data, save_output
from loguru import logger

if __name__ == "__main__":
    config = load_config()
    input_dir = config['input_directory']
    output_dir = config['output_directory']

    os.makedirs(output_dir, exist_ok=True)
    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]

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
