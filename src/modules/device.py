from socket import create_connection

def has_internet_connection():
    """Does Device has Internet connection"""
    try:
        create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False