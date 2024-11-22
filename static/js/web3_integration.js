// Web3 Integration for Anti-Doping Platform
let web3;
let userAccount;

// Initialize Web3
async function initWeb3() {
    if (typeof window.ethereum !== 'undefined') {
        try {
            // Request account access
            await window.ethereum.request({ method: 'eth_requestAccounts' });
            web3 = new Web3(window.ethereum);
            
            // Get user's account
            const accounts = await web3.eth.getAccounts();
            userAccount = accounts[0];
            
            // Update UI
            updateWalletStatus(true);
            
            // Listen for account changes
            window.ethereum.on('accountsChanged', function (accounts) {
                userAccount = accounts[0];
                updateWalletStatus(true);
            });

            return true;
        } catch (error) {
            console.error('User denied account access:', error);
            updateWalletStatus(false);
            return false;
        }
    } else {
        console.log('Please install MetaMask!');
        updateWalletStatus(false);
        return false;
    }
}

// Update wallet connection status in UI
function updateWalletStatus(connected) {
    const walletBtn = document.getElementById('wallet-connect');
    const walletStatus = document.getElementById('wallet-status');
    
    if (connected) {
        walletBtn.innerText = 'Wallet Connected';
        walletBtn.classList.remove('btn-primary');
        walletBtn.classList.add('btn-success');
        walletStatus.innerText = `Connected: ${userAccount.substring(0, 6)}...${userAccount.substring(38)}`;
    } else {
        walletBtn.innerText = 'Connect Wallet';
        walletBtn.classList.remove('btn-success');
        walletBtn.classList.add('btn-primary');
        walletStatus.innerText = 'Not Connected';
    }
}

// Connect wallet button click handler
async function connectWallet() {
    await initWeb3();
}

// Get user's wallet address
function getUserWalletAddress() {
    return userAccount;
}

// Verify certificate
async function verifyCertificate(tokenId) {
    try {
        const response = await fetch(`/verify_certificate/${tokenId}`);
        const data = await response.json();
        
        if (data.success) {
            showVerificationResult(data);
        } else {
            showError('Certificate verification failed: ' + data.error);
        }
    } catch (error) {
        showError('Error verifying certificate: ' + error.message);
    }
}

// Show verification result in modal
function showVerificationResult(data) {
    const modal = document.getElementById('verificationModal');
    const modalBody = modal.querySelector('.modal-body');
    
    let html = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Certificate Details</h5>
                <p><strong>Quiz Title:</strong> ${data.data.quiz_title}</p>
                <p><strong>Score:</strong> ${data.data.score}%</p>
                <p><strong>Date Issued:</strong> ${data.data.date}</p>
                <p><strong>Owner:</strong> ${data.owner}</p>
                <p><strong>Valid:</strong> <span class="badge bg-success">Yes</span></p>
            </div>
        </div>
    `;
    
    modalBody.innerHTML = html;
    new bootstrap.Modal(modal).show();
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.insertBefore(errorDiv, document.body.firstChild);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    const walletBtn = document.getElementById('wallet-connect');
    if (walletBtn) {
        walletBtn.addEventListener('click', connectWallet);
    }
});
