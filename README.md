# Blockchain Anti-Doping Educational Platform

A comprehensive blockchain-powered educational platform focused on anti-doping awareness and certification.

## Features

- Interactive Anti-Doping Quiz System
- Blockchain-Verified Certificates
- MetaMask Wallet Integration
- PDF Certificate Generation
- Educational Resources
- AI-Powered Chatbot
- Digital Twin Integration
- Smart Labels
- Podcast System

## Tech Stack

- **Frontend:**
  - HTML5, CSS3, JavaScript
  - Bootstrap 5
  - Web3.js
  - Font Awesome

- **Backend:**
  - Python Flask
  - MongoDB
  - Web3.py
  - OpenAI Integration

- **Blockchain:**
  - Ganache (Local Development)
  - Smart Contracts
  - MetaMask

## Prerequisites

- Python 3.9+
- Node.js and npm
- MongoDB
- Ganache
- MetaMask Browser Extension

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/antidoping-platform.git
cd antidoping-platform
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start Ganache and configure MetaMask:
- Open Ganache
- Import a Ganache account to MetaMask
- Connect MetaMask to Ganache network (http://127.0.0.1:7545)

6. Run the application:
```bash
python app.py
```

7. Access the application:
```
http://localhost:5000
```

## Environment Variables

Copy `.env.example` to `.env` and update the values:

- `MONGODB_URI`: MongoDB connection string
- `DB_NAME`: Database name
- `BLOCKCHAIN_NETWORK`: Blockchain network URL
- `CHAIN_ID`: Network chain ID
- `CONTRACT_ADDRESS`: Deployed contract address
- `SECRET_KEY`: Flask secret key
- `OPENAI_API_KEY`: OpenAI API key (for chatbot)

## Development

1. Make sure to run tests before submitting PR:
```bash
python -m pytest
```

2. Follow the coding style:
```bash
flake8 .
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Smart contract templates
- OpenAI for AI integration
- MetaMask for wallet integration
- Bootstrap for UI components
