document.addEventListener("DOMContentLoaded", function() {
    const timerElement = document.getElementById('timer');
    const finishUrl = timerElement.getAttribute('data-finish-url');
    const sessionId = timerElement.getAttribute('data-session-id');
    const initialDuration = parseInt(timerElement.getAttribute('data-duration'), 10);
    let sessionFinished = timerElement.getAttribute('data-finished') === 'true';

    // Retrieve or initialize the remaining time from localStorage, or set to initial duration
    let remainingTime = parseInt(localStorage.getItem('remainingTime_' + sessionId)) || initialDuration;
    let lastUpdateTime = parseInt(localStorage.getItem('lastUpdateTime_' + sessionId)) || Date.now();

    // Retrieve warning flags from sessionStorage
    let warningShown = sessionStorage.getItem('warningShown') === 'true';
    let warningClosed = sessionStorage.getItem('warningClosed') === 'true';

    // Update the timer display based on the actual elapsed time
    function updateTimer() {
        if (sessionFinished) {
            clearInterval(timerInterval);
            localStorage.removeItem('remainingTime_' + sessionId);
            localStorage.removeItem('lastUpdateTime_' + sessionId);
            return;
        }

        const currentTime = Date.now();
        const elapsedTime = Math.floor((currentTime - lastUpdateTime) / 1000);

        // Update remaining time
        if (elapsedTime > 0) {
            remainingTime -= elapsedTime;
            lastUpdateTime = currentTime;

            if (remainingTime < 0) remainingTime = 0;
            localStorage.setItem('remainingTime_' + sessionId, remainingTime);
            localStorage.setItem('lastUpdateTime_' + sessionId, lastUpdateTime);
        }

        // Update the timer display
        let minutes = Math.floor(remainingTime / 60);
        let seconds = remainingTime % 60;
        timerElement.innerHTML = `Time Remaining: ${minutes}:${seconds < 10 ? '0' + seconds : seconds}`;

        if (remainingTime <= 30 && !warningShown && !warningClosed) {
            showWarningPopup();
            warningShown = true;
            sessionStorage.setItem('warningShown', 'true');
        }

        if (remainingTime <= 0) {
            clearInterval(timerInterval);
            window.location.href = finishUrl;
        }
    }

    function showWarningPopup() {
        if (document.getElementById('warning-popup')) return;

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

        document.getElementById('close-popup').addEventListener('click', function() {
            warningClosed = true;
            sessionStorage.setItem('warningClosed', 'true');
            document.body.removeChild(popup);
        });
    }

    let syncTimeout;
    function syncTimerAcrossTabs(event) {
        if (event.key === 'remainingTime_' + sessionId || event.key === 'lastUpdateTime_' + sessionId) {
            clearTimeout(syncTimeout);
            syncTimeout = setTimeout(() => {
                remainingTime = parseInt(localStorage.getItem('remainingTime_' + sessionId)) || initialDuration;
                lastUpdateTime = parseInt(localStorage.getItem('lastUpdateTime_' + sessionId)) || Date.now();
                updateTimer();
            }, 100); // debounce to prevent excessive updates
        }
    }

    window.addEventListener('storage', syncTimerAcrossTabs);

    const timerInterval = setInterval(updateTimer, 1000);
    updateTimer(); // Initial call to set the timer display correctly

    const chatForm = document.getElementById('chat-form');
    const sendButton = document.getElementById('send-button');
    if (chatForm) {
        chatForm.addEventListener('submit', function() {
            sendButton.disabled = true;
            const remainingTimeInput = document.createElement('input');
            remainingTimeInput.type = 'hidden';
            remainingTimeInput.name = 'remaining_time';
            remainingTimeInput.value = remainingTime;
            chatForm.appendChild(remainingTimeInput);
            localStorage.setItem('remainingTime_' + sessionId, remainingTime);
        });
    }

    if (!localStorage.getItem('remainingTime_' + sessionId)) {
        localStorage.setItem('remainingTime_' + sessionId, remainingTime);
        localStorage.setItem('lastUpdateTime_' + sessionId, lastUpdateTime);
    }
});
