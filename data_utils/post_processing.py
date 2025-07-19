import argparse
import json
import shutil
from pathlib import Path
from multiprocessing import Pool, cpu_count
import tqdm

def is_valid_json_structure(file_path):
    """Check if the JSON file has the expected structure."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            
            # Check if required keys exist in the top-level structure
            if not all(key in data for key in ["name", "objects", "roads", "tl_states"]):
                return False
                
            # Check if "objects" is a list and contains dictionaries with the correct structure
            if not isinstance(data["objects"], list) or not all(
                isinstance(obj, dict) and "position" in obj and "type" in obj
                for obj in data["objects"]
            ):
                return False
                
            # Check if "roads" is a list of dictionaries with required "geometry"
            if not isinstance(data["roads"], list) or not all(
                isinstance(road, dict) and "geometry" in road
                for road in data["roads"]
            ):
                return False
                
            # Check that each "geometry" in "roads" has valid "x" and "y" coordinates
            for road in data["roads"]:
                if not all(
                    isinstance(geo, dict) and "x" in geo and "y" in geo
                    for geo in road.get("geometry", [])
                ):
                    return False
                    
            return True
    except (json.JSONDecodeError, ValueError, IOError):
        return False

def process_file(args):
    """
    Validate JSON file and copy it to target directory if valid.
    
    Args:
        args (tuple): (source_path, target_dir, should_copy)
            - source_path: Path to the source file
            - target_dir: Path to target directory (if copying)
            - should_copy: Boolean indicating if file should be copied if valid
    Returns:
        tuple: (str, bool) - (file path, whether file was valid)
    """
    source_path, target_dir, should_copy = args
    
    # First validate the JSON
    if not is_valid_json_structure(source_path):
        print(f"Invalid JSON file: {source_path}")
        return str(source_path), False
    
    # If valid and should_copy is True, copy the file
    if should_copy and target_dir:
        try:
            target_path = Path(target_dir) / source_path.name
            # Create target directory if it doesn't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if target file already exists
            if target_path.exists():
                print(f"Warning: Target file already exists, skipping: {target_path}")
                return str(source_path), True
            
            # Copy the file instead of moving
            shutil.copy2(str(source_path), str(target_path))
            print(f"Copied: {source_path} -> {target_path}")
        except Exception as e:
            print(f"Error copying file {source_path}: {e}")
            return str(source_path), False
    
    return str(source_path), True

def process_directory(dataset_dir, target_base_dir=None, num_workers=None):
    """
    Process all JSON files in a directory, copying valid files to target directory.
    
    Args:
        dataset_dir (str): Path to the dataset directory
        target_base_dir (str, optional): Base directory to copy processed files to
        num_workers (int, optional): Number of processes to use. Defaults to CPU count.
    Returns:
        tuple: (int, int) - (valid_files, invalid_files)
    """
    dataset_path = Path(dataset_dir)
    
    if not dataset_path.is_dir():
        print(f"Directory {dataset_dir} does not exist, skipping...")
        return 0, 0
    
    # Determine target directory
    if target_base_dir:
        # Extract the subdirectory name (training/testing/validation) from the source path
        subdir_name = dataset_path.name
        target_dir = Path(target_base_dir) / subdir_name
    else:
        target_dir = dataset_path
    
    # Check for group directories
    group_dirs = [d for d in dataset_path.iterdir() 
                 if d.is_dir() and d.name.startswith("group_")]
    
    # Collect all files that need to be processed
    all_files = []
    
    if group_dirs:
        # Found group directories - will copy files from them
        print(f"\nFound {len(group_dirs)} group directories in {dataset_dir}")
        for group_dir in sorted(group_dirs):
            files = list(group_dir.glob("*.json"))
            all_files.extend([(file, target_dir, True) for file in files])
    
    # Always check for JSON files in the main directory as well
    main_dir_files = [f for f in dataset_path.glob("*.json") 
                     if not any(g.name in str(f) for g in group_dirs)]
    all_files.extend([(file, target_dir, True) for file in main_dir_files])
    
    total_files = len(all_files)
    if total_files == 0:
        print(f"No JSON files found in {dataset_dir}")
        return 0, 0
    
    print(f"Total files to process: {total_files}")
    if target_base_dir:
        print(f"Valid files will be copied to: {target_dir}")
    
    # Use all available CPUs if num_workers is not specified
    if num_workers is None:
        num_workers = cpu_count()
    
    # Track statistics
    valid_files = 0
    invalid_files = 0
    
    # Create a pool of workers and process files in parallel
    with Pool(processes=num_workers) as pool:
        # Use tqdm to show progress bar
        results = list(tqdm.tqdm(
            pool.imap_unordered(process_file, all_files),
            total=total_files,
            desc=f"Processing files from {dataset_dir}"
        ))
        
        # Count valid and invalid files
        for _, is_valid in results:
            if is_valid:
                valid_files += 1
            else:
                invalid_files += 1
    
    print(f"\nCompleted processing {dataset_dir}")
    print(f"Valid files copied: {valid_files}")
    print(f"Invalid files skipped: {invalid_files}")
    
    return valid_files, invalid_files

def process_all_directories(source_base_dir, target_base_dir=None, num_workers=None):
    """Process all dataset directories (training, testing, validation)."""
    directories = [
        f"{source_base_dir}/training",
        f"{source_base_dir}/testing", 
        f"{source_base_dir}/validation"
    ]
    
    total_valid = 0
    total_invalid = 0
    
    for directory in directories:
        print(f"\nProcessing directory: {directory}")
        valid, invalid = process_directory(directory, target_base_dir, num_workers)
        total_valid += valid
        total_invalid += invalid
    
    print("\nOverall Statistics:")
    print(f"Total valid files copied across all directories: {total_valid}")
    print(f"Total invalid files skipped: {total_invalid}")
    print(f"Total files processed: {total_valid + total_invalid}")

def main():
    parser = argparse.ArgumentParser(
        description="Process JSON files in dataset directories, validating their structure and "
                  "copying valid files to target directory. Original files remain unchanged. "
                  'Use "all" to process training, testing, and validation directories.'
    )
    parser.add_argument(
        "dataset_dir",
        nargs="?",
        default="all",
        help='Path to the dataset directory or "all" for processing all directories'
    )
    parser.add_argument(
        "--target_dir",
        type=str,
        required=True,
        help="Target directory to copy processed files to (e.g., data/raw)"
    )
    parser.add_argument(
        "--num_workers",
        type=int,
        help="Number of processes to use (defaults to number of CPU cores)",
        default=cpu_count()
    )
    
    args = parser.parse_args()
    
    try:
        if args.dataset_dir.lower() == "all":
            # For "all" mode, we need to specify the source base directory
            print("Error: When using 'all' mode, please specify the full path to the dataset directory")
            print("Example: python post_processing.py /mnt/dataset/GPUDrive --target_dir data/raw")
            return 1
        else:
            # Check if the specified directory contains training/testing/validation subdirectories
            dataset_path = Path(args.dataset_dir)
            if dataset_path.is_dir():
                subdirs = [d.name for d in dataset_path.iterdir() 
                          if d.is_dir() and d.name in ["training", "testing", "validation"]]
                
                if subdirs:
                    # This is a base directory with subdirectories, process all
                    print(f"Found subdirectories: {subdirs}")
                    process_all_directories(args.dataset_dir, args.target_dir, args.num_workers)
                else:
                    # This is a single directory, process it
                    process_directory(args.dataset_dir, args.target_dir, args.num_workers)
            else:
                print(f"Directory {args.dataset_dir} does not exist")
                return 1
                
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
