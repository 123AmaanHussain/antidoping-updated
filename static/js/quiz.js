// Global variables
let currentQuiz = null;
let userAnswers = [];
let userId = null;
let walletState = {
    connected: false,
    currentAccount: null,
    chainId: null
};

// Initialize Web3
async function initWeb3() {
    if (typeof window.ethereum !== 'undefined') {
        window.web3 = new Web3(window.ethereum);
        return true;
    }
    showError('MetaMask is not installed. Please install MetaMask to continue.');
    return false;
}

// Connect wallet
window.connectWallet = async function() {
    try {
        if (!await initWeb3()) {
            return false;
        }

        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        if (accounts.length === 0) {
            throw new Error('No accounts found.');
        }

        walletState.currentAccount = accounts[0];
        walletState.connected = true;

        // Get network ID
        const chainId = await window.ethereum.request({ method: 'eth_chainId' });
        walletState.chainId = chainId;

        updateWalletUI();
        showSuccess('Wallet connected successfully!');
        return true;
    } catch (error) {
        console.error('Error connecting wallet:', error);
        showError('Failed to connect wallet: ' + error.message);
        return false;
    }
}

// Update wallet UI
function updateWalletUI() {
    const statusElement = document.getElementById('wallet-status');
    const addressElement = document.getElementById('wallet-address');
    const connectButton = document.getElementById('connect-wallet');

    if (walletState.connected && walletState.currentAccount) {
        statusElement.textContent = 'Connected';
        statusElement.className = 'text-success';
        addressElement.textContent = `${walletState.currentAccount.substring(0, 6)}...${walletState.currentAccount.substring(38)}`;
        connectButton.textContent = 'Connected';
        connectButton.disabled = true;
    } else {
        statusElement.textContent = 'Not Connected';
        statusElement.className = 'text-danger';
        addressElement.textContent = '';
        connectButton.textContent = 'Connect Wallet';
        connectButton.disabled = false;
    }
}

// Start quiz
window.startQuiz = async function() {
    try {
        const userIdInput = document.getElementById('user-id');
        if (!userIdInput || !userIdInput.value) {
            showError('Please enter your User ID');
            return;
        }

        if (!walletState.connected) {
            showError('Please connect your wallet first');
            return;
        }

        userId = userIdInput.value;
        const response = await fetch('/get_quiz/quiz1');
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error || 'Failed to load quiz');
        }
        
        currentQuiz = data;
        userAnswers = new Array(currentQuiz.questions.length).fill(null);
        
        displayQuiz(currentQuiz);
        document.getElementById('start-section').style.display = 'none';
        document.getElementById('quiz-container').style.display = 'block';
    } catch (error) {
        console.error('Error starting quiz:', error);
        showError('Failed to start quiz: ' + error.message);
    }
}

// Display quiz
function displayQuiz(quiz) {
    const container = document.getElementById('quiz-container');
    let html = '<form id="quiz-form">';
    
    quiz.questions.forEach((question, index) => {
        html += `
            <div class="question mb-4">
                <p><strong>Question ${index + 1}:</strong> ${question.text}</p>
                <div class="options">
                    ${question.options.map((option, optIndex) => `
                        <div class="form-check">
                            <input class="form-check-input" type="radio" 
                                name="question${index}" 
                                id="q${index}o${optIndex}" 
                                value="${optIndex}"
                                ${userAnswers[index] === optIndex ? 'checked' : ''}
                                onchange="handleAnswer(${index}, ${optIndex})">
                            <label class="form-check-label" for="q${index}o${optIndex}">
                                ${option}
                            </label>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    });
    
    html += `
        <div class="text-center mt-4">
            <button type="button" class="btn btn-primary" onclick="submitQuiz()">Submit Quiz</button>
        </div>
    </form>`;
    
    container.innerHTML = html;
}

// Handle answer selection
window.handleAnswer = function(questionIndex, optionIndex) {
    userAnswers[questionIndex] = optionIndex;
}

// Submit quiz
window.submitQuiz = async function() {
    try {
        if (!userId || !currentQuiz) {
            showError('Invalid quiz session');
            return;
        }

        if (!walletState.connected || !walletState.currentAccount) {
            showError('Please connect your wallet first');
            return;
        }

        const response = await fetch('/submit_quiz', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                quiz_id: currentQuiz.quiz_id,
                answers: userAnswers,
                wallet_address: walletState.currentAccount
            })
        });

        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error || 'Failed to submit quiz');
        }

        document.getElementById('quiz-container').style.display = 'none';
        handleQuizSubmission(result.score, result.certificate);
        showSuccess('Quiz submitted successfully!');

    } catch (error) {
        console.error('Error submitting quiz:', error);
        showError('Failed to submit quiz: ' + error.message);
    }
}

function handleQuizSubmission(score, certificateData) {
    const resultContainer = document.getElementById('quiz-result');
    resultContainer.style.display = 'block';
    
    resultContainer.innerHTML = `
        <div class="alert ${score >= 70 ? 'alert-success' : 'alert-warning'}">
            <h4>Quiz Complete!</h4>
            <p>Your score: ${score}%</p>
            ${score >= 70 ? '<p>Congratulations! You have passed the quiz.</p>' : '<p>Keep trying! You need 70% to pass.</p>'}
        </div>
    `;

    if (certificateData) {
        const certificateSection = document.createElement('div');
        certificateSection.className = 'mt-4';
        
        if (certificateData.pdf_path) {
            const downloadBtn = document.createElement('a');
            downloadBtn.href = `/download_certificate/${userId}/${certificateData.pdf_path}`;
            downloadBtn.className = 'btn btn-primary me-3';
            downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download Certificate';
            certificateSection.appendChild(downloadBtn);
        }

        if (certificateData.token_id) {
            const verifyBtn = document.createElement('button');
            verifyBtn.className = 'btn btn-info';
            verifyBtn.innerHTML = '<i class="fas fa-check-circle"></i> Verify on Blockchain';
            verifyBtn.onclick = () => verifyBlockchainCertificate(certificateData.token_id);
            certificateSection.appendChild(verifyBtn);
        }

        resultContainer.appendChild(certificateSection);
    }

    if (score < 70) {
        const retryBtn = document.createElement('button');
        retryBtn.className = 'btn btn-primary mt-3';
        retryBtn.innerHTML = 'Try Again';
        retryBtn.onclick = startQuiz;
        resultContainer.appendChild(retryBtn);
    }
}

// Helper functions
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 5000);
}

// Listen for account changes
if (window.ethereum) {
    window.ethereum.on('accountsChanged', async (accounts) => {
        if (accounts.length === 0) {
            walletState.connected = false;
            walletState.currentAccount = null;
        } else {
            walletState.currentAccount = accounts[0];
            walletState.connected = true;
        }
        updateWalletUI();
    });

    window.ethereum.on('chainChanged', (chainId) => {
        walletState.chainId = chainId;
        window.location.reload();
    });
}

// Initialize wallet on page load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await connectWallet();
    } catch (error) {
        console.error('Error initializing wallet:', error);
    }
});

// Make functions available globally
window.connectWallet = connectWallet;
window.startQuiz = startQuiz;
window.submitQuiz = submitQuiz;
window.handleAnswer = handleAnswer;
