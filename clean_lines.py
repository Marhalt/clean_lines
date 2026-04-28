import argparse
import os

def normalize_line_breaks(content: str) -> tuple:
    """
    Normalizes hard break characters in the text.
    Replaces Windows (CRLF) and Mac Classic (CR) line endings with standard UNIX (LF).
    Returns a tuple containing the cleaned content, CRLF count, and CR count.
    """
    # Count occurrences before replacing
    crlf_count = content.count('\r\n')
    # Step 1: Replace CRLF (\r\n) with a standard newline (\n) to avoid double spacing
    content = content.replace('\r\n', '\n')
    
    cr_count = content.count('\r')
    # Step 2: Replace any standalone CR (\r) with a standard newline (\n)
    content = content.replace('\r', '\n')
    
    return content, crlf_count, cr_count

def remove_rogue_newlines(content: str) -> str:
    """
    Removes single newlines that break sentences in half, 
    while preserving double newlines used for paragraph breaks.
    """
    # Step 1: Preserve paragraph breaks by replacing double newlines with a placeholder
    content = content.replace('\n\n', '[PLACEHOLDER]')
    # Step 2: Replace remaining single newlines with a space to avoid merging words together
    content = content.replace('\n', ' ')
    # Step 3: Restore the paragraph breaks
    content = content.replace('[PLACEHOLDER]', '\n\n')
    return content

def process_file(file_path: str) -> bool:
    """
    Reads a file, applies text cleaning functions, and saves to a new file.
    """
    if not os.path.isfile(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return False

    # Using utf-8 encoding, though files from "weird places" might occasionally need 'latin-1' or 'cp1252'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Error: Unable to decode '{file_path}'. It may not be a standard UTF-8 text file.")
        return False

    # Apply the line break normalization
    cleaned_content, crlf_count, cr_count = normalize_line_breaks(content)

    # Remove rogue single newlines
    cleaned_content = remove_rogue_newlines(cleaned_content)

    # print(f"Replaced {crlf_count} CRLF (\\r\\n) and {cr_count} CR (\\r) line endings.")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    print(f"Success! Cleaned text overwritten in: '{file_path}'")
    return True

if __name__ == "__main__":
    # Setup the argument parser for a clean command-line interface
    parser = argparse.ArgumentParser(
        description="Clean up downloaded story text files or directories by normalizing wonky line breaks."
    )
    parser.add_argument(
        "path", 
        help="The path to the text file or directory you want to clean"
    )
    
    args = parser.parse_args()
    target_path = args.path

    if os.path.isdir(target_path):
        confirm = input(f"Target '{target_path}' is a directory. Are you sure you want to clean ALL files within it? (y/n): ")
        if confirm.lower() in ['y', 'yes']:
            processed_count = 0
            for item in os.listdir(target_path):
                item_path = os.path.join(target_path, item)
                if os.path.isfile(item_path) and item.lower().endswith('.txt'):
                    if process_file(item_path):
                        processed_count += 1
            print(f"\nDirectory cleaning complete. Total files processed: {processed_count}")
        else:
            print("Operation cancelled.")
    elif os.path.isfile(target_path):
        if target_path.lower().endswith('.txt'):
            process_file(target_path)
        else:
            print(f"Error: The file '{target_path}' is not a .txt file.")
    else:
        print(f"Error: The path '{target_path}' does not exist.")
