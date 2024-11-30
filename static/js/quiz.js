let currentQuestionIndex = 0;
let questions = [];
let userAnswers = [];
let userId = '';

async function startQuiz() {
    userId = document.getElementById('user-id').value.trim();
    if (!userId) {
        showError('Please enter a User ID');
        return;
    }

    try {
        const response = await fetch('/get_questions');
        if (!response.ok) {
            throw new Error('Failed to fetch questions');
        }
        questions = await response.json();
        
        document.getElementById('start-section').style.display = 'none';
        document.getElementById('quiz-container').style.display = 'block';
        displayQuestion();
    } catch (error) {
        showError('Error starting quiz: ' + error.message);
    }
}

function displayQuestion() {
    const question = questions[currentQuestionIndex];
    const quizContainer = document.getElementById('quiz-container');
    
    const html = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Question ${currentQuestionIndex + 1} of ${questions.length}</h5>
                <p class="card-text">${question.question}</p>
                <div class="options">
                    ${question.options.map((option, index) => `
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="radio" name="answer" value="${index}" id="option${index}">
                            <label class="form-check-label" for="option${index}">
                                ${option}
                            </label>
                        </div>
                    `).join('')}
                </div>
                <button onclick="submitAnswer()" class="btn btn-primary mt-3">Submit Answer</button>
            </div>
        </div>
    `;
    
    quizContainer.innerHTML = html;
}

async function submitAnswer() {
    const selectedOption = document.querySelector('input[name="answer"]:checked');
    if (!selectedOption) {
        showError('Please select an answer');
        return;
    }

    userAnswers.push(parseInt(selectedOption.value));

    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        displayQuestion();
    } else {
        await submitQuiz();
    }
}

async function submitQuiz() {
    try {
        const response = await fetch('/submit_quiz', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                answers: userAnswers
            })
        });

        if (!response.ok) {
            throw new Error('Failed to submit quiz');
        }

        const result = await response.json();
        displayResult(result);

    } catch (error) {
        showError('Error submitting quiz: ' + error.message);
    }
}

function displayResult(result) {
    document.getElementById('quiz-container').style.display = 'none';
    const resultContainer = document.getElementById('quiz-result');
    
    const html = `
        <div class="card">
            <div class="card-body text-center">
                <h4 class="card-title">Quiz Complete!</h4>
                <p class="card-text">Your Score: ${result.score}/${questions.length}</p>
                <p class="card-text">Percentage: ${(result.score/questions.length * 100).toFixed(2)}%</p>
                ${result.passed ? 
                    `<div class="alert alert-success">Congratulations! You passed the quiz!</div>
                     <button onclick="downloadCertificate()" class="btn btn-success mt-3">Download Certificate</button>` :
                    `<div class="alert alert-warning">Unfortunately, you didn't pass. Please try again.</div>
                     <button onclick="location.reload()" class="btn btn-primary mt-3">Retry Quiz</button>`
                }
            </div>
        </div>
    `;
    
    resultContainer.innerHTML = html;
    resultContainer.style.display = 'block';
}

async function downloadCertificate() {
    try {
        const response = await fetch(`/download_certificate/${userId}`);
        if (!response.ok) {
            throw new Error('Failed to download certificate');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `certificate_${userId}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        showError('Error downloading certificate: ' + error.message);
    }
}

function showError(message) {
    const errorElement = document.getElementById('error-message');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}
