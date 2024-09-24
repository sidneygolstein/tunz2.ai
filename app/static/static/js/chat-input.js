document.addEventListener("DOMContentLoaded", function() {
    const textarea = document.getElementById("chat-textarea");
    const form = document.getElementById("chat-form");
    const sendButton = document.getElementById("send-button");
    const chatBox = document.getElementById("chat-box");

    textarea.addEventListener("input", function() {
        // Reset the height to calculate the new height
        textarea.style.height = 'auto';

        // Calculate the new height (up to a maximum of 100px)
        const maxHeight = 100; // Same as the max-height in the CSS
        if (textarea.scrollHeight <= maxHeight) {
            textarea.style.height = textarea.scrollHeight + 'px';
        } else {
            textarea.style.height = maxHeight + 'px'; // Set to the max height
        }
    });

    // Prevent form submission on Enter key, allow line breaks
    textarea.addEventListener("keydown", function(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault(); // Prevent submission on Enter
        }
    });


    // Form submission logic
    form.addEventListener("submit", function(event) {
        event.preventDefault();

        // Stop the current audio if any
        window.stopCurrentAudio();

        const userAnswer = textarea.value;
        displayMessage(userAnswer, 'user');
        disableSendButton();
        displayTypingIndicator();

        const formData = new FormData(form);
        textarea.value = '';
        textarea.style.height = 'auto';
        textarea.placeholder = "Please enter your answer";

        // Fetch the response
        fetch(form.action, {
            method: 'POST',
            body: formData
        }).then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const lastQuestionElement = doc.querySelectorAll("#chat-box .message.assistant p");

            if (lastQuestionElement && lastQuestionElement.length > 0) {
                const newQuestion = lastQuestionElement[lastQuestionElement.length - 1].innerHTML;
                replaceTypingIndicator(newQuestion);
                enableSendButton();

                // Get the latest question ID
                const latestAssistantContainer = doc.querySelectorAll('.assistant-container:last-of-type')[0];
                const latestQuestionId = latestAssistantContainer.getAttribute('data-question-id');
                

                // Reconstruct the audio file path
                const audioFilePath = latestAssistantContainer.getAttribute('data-file-path');
                console.log(`Reconstructed audio file path: ${audioFilePath}`);

                console.log(`Detected latestQuestionId: ${latestQuestionId}`);
                console.log(`Detected audiFilePath: ${audioFilePath}`);

                // Directly play the audio using the file path
                createAndPlayAudio(audioFilePath);
            } else {
                console.error("chat-input: No new question received.");
                enableSendButton();
            }
        })
        .catch(error => {
            console.error("chat-input: Failed to send message:", error);
            enableSendButton();
        });
    });


    // Function to dynamically create and play the audio
    function createAndPlayAudio(audioFilePath) {
        const audioElement = new Audio(audioFilePath);  // Create a new audio element
        audioElement.addEventListener('loadedmetadata', () => {
            console.log(`Audio metadata loaded for: ${audioFilePath}`);
            window.playNewAudio(audioElement);  // Call the global playNewAudio function
        });
    }

    







    function sortMessagesByTimestamp() {
        const messageContainers = Array.from(chatBox.querySelectorAll('.message-container'));
        messageContainers.sort((a, b) => {
            const timestampA = parseInt(a.dataset.timestamp, 10);
            const timestampB = parseInt(b.dataset.timestamp, 10);
            return timestampA - timestampB;
        });

        // Clear the chat box and re-append messages in sorted order
        chatBox.innerHTML = '';
        messageContainers.forEach(container => chatBox.appendChild(container));
    }

    function displayMessage(message, role) {
        // Replace double newline characters (\n\n) with two <br> tags for paragraph breaks
        let formattedMessage = message.replace(/\n\n/g, '<br><br>');

        // Replace single newline characters (\n) with a single <br> tag for line breaks
        formattedMessage = formattedMessage.replace(/\n/g, '<br>');

        // Create the message container
        const messageContainer = document.createElement("div");
        messageContainer.classList.add("message-container", `${role}-container`);

        // Generate a timestamp
        const timestamp = Date.now();
        messageContainer.dataset.timestamp = timestamp; // Add timestamp as a data attribute

        // Create the message element
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", role);
        messageElement.innerHTML = `<p>${formattedMessage}</p>`;

        // Add the appropriate icon for assistant or user
        if (role === 'assistant') {
            const assistantIcon = document.createElement("img");
            assistantIcon.src = '/static/static/andy.png'; // Adjust the path as needed
            assistantIcon.classList.add("message-icon");
            messageContainer.appendChild(assistantIcon); // Add icon first
            messageContainer.appendChild(messageElement); // Then add the message
        } else if (role === 'user') {
            const userIcon = document.createElement("img");
            userIcon.src = '/static/static/user_icon.png'; // Adjust the path as needed
            userIcon.classList.add("message-icon");
            messageContainer.appendChild(messageElement); // Add the message first
            messageContainer.appendChild(userIcon); // Then add the icon
        }

        // Append the entire message container to the chat box
        chatBox.appendChild(messageContainer);

        // Sort messages by timestamp after appending the new message
        sortMessagesByTimestamp();

        // Scroll to the bottom of the chat box
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function displayTypingIndicator() {
        // Create the "Typing..." indicator
        const typingContainer = document.createElement("div");
        typingContainer.classList.add("message-container", "assistant-container", "typing-indicator");
        typingContainer.id = "typing-indicator"; // Assign an ID to find and replace later

        // Add a timestamp to the typing indicator for proper sorting
        typingContainer.dataset.timestamp = Date.now(); 

        // Create the message element with "Typing..." text
        const typingElement = document.createElement("div");
        typingElement.classList.add("message", "assistant");
        typingElement.innerHTML = `<p>Typing...</p>`;

        // Add the Andy icon
        const assistantIcon = document.createElement("img");
        assistantIcon.src = '/static/static/andy.png'; // Adjust the path as needed
        assistantIcon.classList.add("message-icon");

        typingContainer.appendChild(assistantIcon); // Add icon first
        typingContainer.appendChild(typingElement); // Then add the "Typing..." message

        // Append the typing indicator to the chat box
        chatBox.appendChild(typingContainer);

        // Sort messages by timestamp after appending the typing indicator
        sortMessagesByTimestamp();

        // Scroll to the bottom of the chat box
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function replaceTypingIndicator(message) {
        const typingIndicator = document.getElementById("typing-indicator");

        if (typingIndicator) {
            const messageElement = typingIndicator.querySelector(".message.assistant p");
            if (messageElement) {
                // Replace "Typing..." with the assistant's response
                messageElement.innerHTML = message;

                // Reset the styles to the normal assistant message styles
                typingIndicator.classList.remove("typing-indicator"); // Remove the typing-indicator class
                messageElement.style.fontStyle = "normal"; // Reset font style
                typingIndicator.querySelector("img.message-icon").style.opacity = "1"; // Reset icon opacity
            }

            // Remove the typing indicator ID to prevent further manipulation
            typingIndicator.removeAttribute("id");
        }
    }

    function disableSendButton() {
        sendButton.disabled = true;
        sendButton.style.backgroundColor = "#2d005e";
    }

    function enableSendButton() {
        sendButton.disabled = false;
        sendButton.style.backgroundColor = "#515BD4"; // Correct hex color code
    }
});

// ANTI FRAUD STRATEGIES: 

document.addEventListener("DOMContentLoaded", function() {
    const textarea = document.getElementById("chat-textarea");
    const form = document.getElementById("chat-form");
    const sendButton = document.getElementById("send-button");
    const chatBox = document.getElementById("chat-box");
    let questionTimestamp;

    // Disable pasting
    textarea.addEventListener('paste', function(event) {
        event.preventDefault();
        alert("Unfortunatelly, pasting is disabled during this interview");
    });



// Disable right click

document.addEventListener('contextmenu', function(event) {
    event.preventDefault();
    alert("Unfortunatelly, right click is disabled during this interview.");
});


// Detecting window switch
window.addEventListener('blur', function() {
    alert("Leaving the chat window is not allowed during this interview.");
});
 
});