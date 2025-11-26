"""
Utility functions for cross-platform compatibility and common operations
"""
import os
import platform
from pathlib import Path


def get_platform():
    """
    Detect the current platform.
    
    Returns:
        str: 'windows', 'linux', or 'darwin' (macOS)
    """
    # Check environment variable override first
    env_platform = os.environ.get('PLATFORM_OS', '').lower()
    if env_platform in ['windows', 'linux', 'darwin']:
        return env_platform
    
    # Auto-detect from system
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    elif system == 'darwin':
        return 'darwin'
    else:
        # Default to linux for unknown systems
        return 'linux'


def get_video_directory():
    """
    Get the appropriate video directory based on the platform.
    
    Priority:
    1. VIDEO_DIRECTORY environment variable (if set)
    2. Platform-specific default directories
    
    Returns:
        Path: Path object pointing to the video directory
    """
    # Check for custom directory in environment
    custom_dir = os.environ.get('VIDEO_DIRECTORY', '').strip()
    if custom_dir:
        return Path(custom_dir).expanduser()
    
    # Platform-specific defaults
    current_platform = get_platform()
    
    if current_platform == 'windows':
        # Windows: ~/Videos
        return Path.home() / "Videos"
    
    elif current_platform == 'darwin':
        # macOS: ~/Movies
        return Path.home() / "Movies"
    
    else:  # linux
        # Linux: Check XDG_VIDEOS_DIR or default to ~/Videos
        xdg_videos = os.environ.get('XDG_VIDEOS_DIR', '').strip()
        if xdg_videos:
            return Path(xdg_videos)
        return Path.home() / "Videos"


def ensure_directory_exists(directory):
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory (Path or str): Directory path to check/create
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory}: {e}")
        return False


def sanitize_filename(filename):
    """
    Sanitize a filename by removing or replacing invalid characters.
    
    Args:
        filename (str): The filename to sanitize
        
    Returns:
        str: Sanitized filename safe for all platforms
    """
    # Characters that are invalid in Windows (most restrictive)
    invalid_chars = '<>:"/\\|?*'
    
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    # Limit length (Windows has 255 char limit for filenames)
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized or 'unnamed'


def get_logs_directory():
    """
    Get the logs directory, creating it if necessary.
    
    Returns:
        Path: Path to logs directory
    """
    logs_dir = Path(__file__).parent.parent / 'logs'
    ensure_directory_exists(logs_dir)
    return logs_dir


def get_config_file_path():
    """
    Get the configuration file path.
    
    Returns:
        Path: Path to configuration file
    """
    config_file = os.environ.get('CONFIG_FILE', 'tiktok_obs_config.json')
    return Path(__file__).parent.parent / config_file
