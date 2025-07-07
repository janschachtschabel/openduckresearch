import os
import shutil
from typing import List
from loguru import logger

def cleanup_folders(folders: List[str], create: bool = True) -> None:
    """
    Leert die angegebenen Ordner und erstellt sie neu, falls sie nicht existieren.
    
    Args:
        folders: Liste der zu bereinigenden Ordnerpfade
        create: Wenn True, werden die Ordner nach dem Löschen neu erstellt
    """
    for folder in folders:
        try:
            if os.path.exists(folder):
                # Lösche den gesamten Ordnerinhalt
                shutil.rmtree(folder)
                logger.info(f"Ordner {folder} wurde geleert")
            
            if create:
                # Erstelle den Ordner neu
                os.makedirs(folder, exist_ok=True)
                logger.info(f"Ordner {folder} wurde neu erstellt")
                
        except Exception as e:
            logger.error(f"Fehler beim Bereinigen von {folder}: {str(e)}")
            
def get_folder_size(folder: str) -> int:
    """
    Berechnet die Größe eines Ordners in Bytes.
    
    Args:
        folder: Pfad zum Ordner
    
    Returns:
        Größe des Ordners in Bytes
    """
    total_size = 0
    if os.path.exists(folder):
        for dirpath, _, filenames in os.walk(folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
    return total_size

def format_size(size_in_bytes: int) -> str:
    """
    Formatiert eine Größe in Bytes in eine lesbare Form.
    
    Args:
        size_in_bytes: Größe in Bytes
    
    Returns:
        Formatierte Größe (z.B. "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} TB"
