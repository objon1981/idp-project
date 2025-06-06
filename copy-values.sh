#!/bin/bash

# Folder containing the common environment values files
COMMON_VALUES_DIR="base-values"

# Base folder containing all your service charts
SERVICES_DIR="helm-base-charts"

# List of environment values files you want to copy
env_files=("values-dev.yaml" "values-staging.yaml" "values-prod.yaml")

# Loop through each service folder inside helm-base-charts
for service_folder in "$SERVICES_DIR"/*; do
  # Check if it's a directory
  if [ -d "$service_folder" ]; then
    echo "Processing service folder: $service_folder"

    # Loop through each environment values file
    for env_file in "${env_files[@]}"; do
      # Source file path
      src_file="$COMMON_VALUES_DIR/$env_file"
      # Destination file path
      dest_file="$service_folder/$env_file"

      # Check if the source file exists before copying
      if [ ! -f "$src_file" ]; then
        echo "Warning: Source file $src_file does not exist! Skipping."
        continue
      fi

      # Copy only if the destination file does NOT exist
      if [ ! -f "$dest_file" ]; then
        cp "$src_file" "$dest_file"
        echo "Copied $env_file to $service_folder"
      else
        echo "Skipped $env_file for $service_folder (already exists)"
      fi
    done

  else
    echo "Skipping $service_folder because it is not a directory"
  fi
done
