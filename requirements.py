import subprocess
import sys
import os

def install_requirements():
    # List of required packages with their versions
    requirements = [
        'flask==2.0.1',
        'pymongo==4.3.3',
        'requests==2.31.0',
        'python-dotenv==0.19.0',
        'spotipy==2.19.0',
        'google-api-python-client==2.86.0',
        'mutagen==1.45.1',
        'flask-cors==4.0.0',
        'python-dateutil==2.8.2',
        'Werkzeug==2.0.1',
        'Pillow==9.5.0',
        'opencv-python==4.7.0.72',
        'numpy==1.24.3',
        'pandas==2.0.2',
        'scikit-learn==1.2.2',
        'tensorflow==2.12.0',
        'torch==2.0.1',
        'transformers==4.29.2',
        'nltk==3.8.1',
        'beautifulsoup4==4.12.2',
        'PyPDF2==3.0.1',
        'python-docx==0.8.11',
        'openpyxl==3.1.2',
        'pyttsx3==2.90',
        'SpeechRecognition==3.10.0'
    ]

    print("Starting installation of required packages...")
    print("This may take a few minutes...")
    
    # Check if pip is installed
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"])
    except subprocess.CalledProcessError:
        print("pip is not installed. Please install pip first.")
        return

    # Upgrade pip
    print("\nUpgrading pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError:
        print("Failed to upgrade pip. Continuing with package installation...")

    # Install each package
    success_count = 0
    failed_packages = []

    for package in requirements:
        package_name = package.split('==')[0]
        print(f"\nInstalling {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            success_count += 1
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError:
            failed_packages.append(package)
            print(f"Failed to install {package}")

    # Installation summary
    print("\n" + "="*50)
    print("Installation Summary:")
    print(f"Successfully installed: {success_count}/{len(requirements)} packages")
    
    if failed_packages:
        print("\nFailed to install the following packages:")
        for package in failed_packages:
            print(f"- {package}")
        print("\nPlease try installing these packages manually or check for any errors.")
    else:
        print("\nAll packages were installed successfully!")

    print("\nNote: Some packages might require additional system dependencies.")
    print("If you encounter any issues, please refer to the package documentation.")
    print("="*50)

if __name__ == "__main__":
    try:
        install_requirements()
        input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\nInstallation interrupted by user.")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
        input("Press Enter to exit...")