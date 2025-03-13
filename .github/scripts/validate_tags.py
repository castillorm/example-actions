import os
import re
import sys

# Path to the tagging data file
TAGGING_FILE = "tagging_data.txt"
TERRAFORM_DIR = "."

# Load valid tags
valid_teams = set()
valid_components = set()
valid_services = set()

# Read the tagging data
with open(TAGGING_FILE, "r") as file:
    for line in file:
        line = line.strip()
        if line.startswith("team:"):
            valid_teams.add(line.split(":")[1])
        elif line.startswith("component:"):
            valid_components.add(line.split(":")[1])
        elif line.startswith("service:"):
            valid_services.add(line.split(":")[1])

# Function to validate Terraform files
def validate_terraform_tags():
    errors = []
    for root, _, files in os.walk(TERRAFORM_DIR):
        for file in files:
            if file.endswith(".tf"):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    content = f.read()
                    aws_resources = re.findall(r'resource\s+"aws_[^"]+"\s+"[^"]+"\s+{(.*?)}', content, re.DOTALL)
                    
                    for resource in aws_resources:
                        tags_match = re.search(r'tags\s*=\s*{(.*?)}', resource, re.DOTALL)
                        if tags_match:
                            tags_content = tags_match.group(1)
                            tags = dict(re.findall(r'"([^"]+)"\s*=\s*"([^"]+)"', tags_content))

                            # Check required tags
                            for key, valid_values in [("team", valid_teams), ("component", valid_components), ("service", valid_services)]:
                                if key not in tags:
                                    errors.append(f"Missing required tag '{key}' in file {file_path}")
                                elif tags[key] not in valid_values:
                                    errors.append(f"Invalid value '{tags[key]}' for tag '{key}' in file {file_path}")

                        else:
                            errors.append(f"Missing 'tags' block in AWS resource in file {file_path}")

    return errors


# Run validation and output results
errors = validate_terraform_tags()

if errors:
    print("\nTagging validation failed:\n")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)  # Exit with error to fail the GitHub Action
else:
    print("All Terraform AWS resource tags are valid!")

