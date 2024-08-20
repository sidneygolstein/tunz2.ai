document.addEventListener("DOMContentLoaded", function() {
    const timerElement = document.getElementById('timer');
    const finishUrl = timerElement.getAttribute('data-finish-url');
    const sessionId = timerElement.getAttribute('data-session-id');
    const initialDuration = parseInt(timerElement.getAttribute('data-duration'), 10);
    let sessionFinished = timerElement.getAttribute('data-finished') === 'true';

    // Retrieve or initialize the remaining time from localStorage, or set to initial duration
    let remainingTime = parseInt(localStorage.getItem('remainingTime_' + sessionId)) || initialDuration;

    // Retrieve warning flags from sessionStorage
    let warningShown = sessionStorage.getItem('warningShown') === 'true';
    let warningClosed = sessionStorage.getItem('warningClosed') === 'true';

    // Update the timer display
    function updateTimer() {
        if (sessionFinished) {
            clearInterval(timerInterval);
            localStorage.removeItem('remainingTime_' + sessionId); // Clear storage on finish
            return;
        }

        let minutes = Math.floor(remainingTime / 60);
        let seconds = remainingTime % 60;
        timerElement.innerHTML = `Time Remaining: ${minutes}:${seconds < 10 ? '0' + seconds : seconds}`;

        if (remainingTime <= 30 && !warningShown && !warningClosed) {
            showWarningPopup();
            warningShown = true;
            sessionStorage.setItem('warningShown', 'true');
        }

        if (remainingTime <= 0) {
            remainingTime = 0;
            clearInterval(timerInterval);
            localStorage.removeItem('remainingTime_' + sessionId);
            window.location.href = finishUrl;
        } else {
            remainingTime -= 1;
            localStorage.setItem('remainingTime_' + sessionId, remainingTime); // Store the updated remaining time
        }
    }

    // Function to handle the warning popup display
    function showWarningPopup() {
        if (document.getElementById('warning-popup')) {
            return; // If the popup already exists, do nothing
        }

        const popup = document.createElement('div');
        popup.id = 'warning-popup';
        popup.classList.add('popup');
        popup.innerHTML = `
            <div class="popup-content">
                <p>You have 30 seconds left to finish your answer.</p>
                <button id="close-popup">Close</button>
            </div>
        `;
        document.body.appendChild(popup);

        const closeButton = document.getElementById('close-popup');
        closeButton.addEventListener('click', function() {
            warningClosed = true;
            sessionStorage.setItem('warningClosed', 'true');
            document.body.removeChild(popup);
        });
    }

    // Synchronize across tabs
    function syncTimerAcrossTabs(event) {
        if (event.key === 'remainingTime_' + sessionId) {
            remainingTime = parseInt(localStorage.getItem('remainingTime_' + sessionId)) || initialDuration;
        }
    }

    window.addEventListener('storage', syncTimerAcrossTabs);

    const timerInterval = setInterval(updateTimer, 1000);
    updateTimer(); // Initial call to set the timer display correctly

    // Attach the remaining time to the form submission
    const chatForm = document.getElementById('chat-form');
    const sendButton = document.getElementById('send-button');
    if (chatForm) {
        chatForm.addEventListener('submit', function() {
            sendButton.disabled = true; // Disable send button on form submission
            const remainingTimeInput = document.createElement('input');
            remainingTimeInput.type = 'hidden';
            remainingTimeInput.name = 'remaining_time';
            remainingTimeInput.value = remainingTime; // Attach current remaining time
            chatForm.appendChild(remainingTimeInput);

            // Ensure that the remaining time is saved before submission
            localStorage.setItem('remainingTime_' + sessionId, remainingTime);
        });
    }

    // Store the remaining time in localStorage if it's not already stored
    if (!localStorage.getItem('remainingTime_' + sessionId)) {
        localStorage.setItem('remainingTime_' + sessionId, remainingTime);
    }
});
