"""
Local forecast file cleanup utilities.

Provides async cleanup functionality for temporary forecast files
stored locally before/after database upload.
"""

import os
import time
import asyncio
import logging
from typing import Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
CLEANUP_MAX_AGE_DAYS = int(os.getenv("FORECAST_CLEANUP_DAYS", "7"))


async def cleanup_old_forecast_files_async(
    output_dir: str = OUTPUT_DIR,
    max_age_days: int = CLEANUP_MAX_AGE_DAYS
) -> None:
    """
    Asynchronously cleanup forecast files older than max_age_days.
    Logs cleanup status but does not return any value.
    
    This function scans all subdirectories in the output directory and
    removes files (text and audio) that are older than the specified age.
    
    Args:
        output_dir: Directory containing forecast files (default: from OUTPUT_DIR env var)
        max_age_days: Maximum age in days before deletion (default: from FORECAST_CLEANUP_DAYS env var)
    
    Returns:
        None - Results are logged only
    """
    try:
        def _cleanup_files() -> Tuple[int, int]:
            """
            Internal function to perform file cleanup.
            
            Returns:
                Tuple of (deleted_files_count, bytes_freed)
            """
            deleted_files = 0
            bytes_freed = 0
            deleted_dirs = 0
            max_age_seconds = max_age_days * 86400  # Convert days to seconds
            now = time.time()
            
            # Check if output directory exists
            if not os.path.exists(output_dir):
                logging.debug(f"Output directory does not exist: {output_dir}")
                return 0, 0
            
            # Scan all city subdirectories
            for city_dir in os.listdir(output_dir):
                city_path = os.path.join(output_dir, city_dir)
                
                # Only process directories
                if not os.path.isdir(city_path):
                    continue
                
                # Scan files in city directory
                for filename in os.listdir(city_path):
                    file_path = os.path.join(city_path, filename)
                    
                    # Only process files (not subdirectories)
                    if not os.path.isfile(file_path):
                        continue
                    
                    try:
                        # Check file age
                        file_age = now - os.path.getmtime(file_path)
                        
                        if file_age > max_age_seconds:
                            # File is old enough to delete
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_files += 1
                            bytes_freed += file_size
                            logging.debug(f"Deleted old file: {file_path} (age: {file_age / 86400:.1f} days)")
                    
                    except Exception as e:
                        # Log individual file errors but continue cleanup
                        logging.warning(f"Failed to delete {file_path}: {str(e)}")
                
                # After processing all files, check if directory is empty and remove it
                try:
                    if not os.listdir(city_path):
                        os.rmdir(city_path)
                        deleted_dirs += 1
                        logging.debug(f"Removed empty directory: {city_path}")
                except Exception as e:
                    logging.warning(f"Failed to remove empty directory {city_path}: {str(e)}")
            
            # Log directory cleanup if any occurred
            if deleted_dirs > 0:
                logging.info(f"Removed {deleted_dirs} empty directories")
            
            return deleted_files, bytes_freed
        
        # Run file I/O in thread pool to avoid blocking event loop
        deleted, freed = await asyncio.to_thread(_cleanup_files)
        
        # Log cleanup results
        if deleted > 0:
            logging.info(
                f"Forecast cleanup completed: {deleted} files deleted, "
                f"{freed / 1024:.2f} KB freed (files older than {max_age_days} days)"
            )
        else:
            logging.debug(f"Forecast cleanup: No files older than {max_age_days} days found")
        
    except Exception as e:
        logging.error(f"Forecast cleanup failed: {str(e)}")


def cleanup_old_forecast_files_sync(
    output_dir: str = OUTPUT_DIR,
    max_age_days: int = CLEANUP_MAX_AGE_DAYS
) -> Tuple[int, int]:
    """
    Synchronous version of cleanup for non-async contexts.
    
    Args:
        output_dir: Directory containing forecast files
        max_age_days: Maximum age in days before deletion
    
    Returns:
        Tuple of (deleted_files_count, bytes_freed)
    """
    deleted_files = 0
    bytes_freed = 0
    deleted_dirs = 0
    max_age_seconds = max_age_days * 86400
    now = time.time()
    
    try:
        if not os.path.exists(output_dir):
            logging.debug(f"Output directory does not exist: {output_dir}")
            return 0, 0
        
        for city_dir in os.listdir(output_dir):
            city_path = os.path.join(output_dir, city_dir)
            
            if not os.path.isdir(city_path):
                continue
            
            for filename in os.listdir(city_path):
                file_path = os.path.join(city_path, filename)
                
                if not os.path.isfile(file_path):
                    continue
                
                try:
                    file_age = now - os.path.getmtime(file_path)
                    
                    if file_age > max_age_seconds:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_files += 1
                        bytes_freed += file_size
                        logging.debug(f"Deleted old file: {file_path} (age: {file_age / 86400:.1f} days)")
                
                except Exception as e:
                    logging.warning(f"Failed to delete {file_path}: {str(e)}")
            
            # After processing all files, check if directory is empty and remove it
            try:
                if not os.listdir(city_path):
                    os.rmdir(city_path)
                    deleted_dirs += 1
                    logging.debug(f"Removed empty directory: {city_path}")
            except Exception as e:
                logging.warning(f"Failed to remove empty directory {city_path}: {str(e)}")
        
        if deleted_files > 0:
            logging.info(
                f"Forecast cleanup completed: {deleted_files} files deleted, "
                f"{bytes_freed / 1024:.2f} KB freed (files older than {max_age_days} days)"
            )
        
        if deleted_dirs > 0:
            logging.info(f"Removed {deleted_dirs} empty directories")
        
        return deleted_files, bytes_freed
    
    except Exception as e:
        logging.error(f"Forecast cleanup failed: {str(e)}")
        return 0, 0
