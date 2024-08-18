document.addEventListener("DOMContentLoaded", function() {
    const textarea = document.getElementById("chat-textarea");
    const form = document.getElementById("chat-form");
    const sendButton = document.getElementById("send-button");
    const chatBox = document.getElementById("chat-box");

    // Resize textarea dynamically
    textarea.addEventListener("input", function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Prevent form submission on Enter key, but allow line breaks
    textarea.addEventListener("keydown", function(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
        }
    });

    // Form submission
    form.addEventListener("submit", function(event) {
        event.preventDefault();
        
        // Display the user's answer immediately
        const userAnswer = textarea.value;
        displayMessage(userAnswer, 'user');

        // Disable the send button
        disableSendButton();

        // Submit the form using fetch to prevent full page reload
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (response.ok) {
                // Wait for the next question and enable the send button
                return response.text();
            } else {
                throw new Error("Failed to send message.");
            }
        }).then(html => {
            // Parse the response HTML and extract the last question
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const lastQuestionElement = doc.querySelectorAll("#chat-box .message.assistant p");

            if (lastQuestionElement && lastQuestionElement.length > 0) {
                const newQuestion = lastQuestionElement[lastQuestionElement.length - 1].textContent;
                
                // Format the assistant's message with line breaks
                const formattedMessage = newQuestion.replace(/\n/g, '<br>');

                // Display the assistant's response
                displayMessage(formattedMessage, 'assistant');
                
                // Clear the textarea and re-enable the send button
                textarea.value = '';
                textarea.style.height = 'auto';
                enableSendButton();
            } else {
                console.error("No new question received.");
                enableSendButton();
            }
        }).catch(error => {
            console.error("Failed to send message:", error);
            enableSendButton();
        });
    });

    function displayMessage(message, role) {
        // Replace double newline characters (\n\n) with two <br> tags for paragraph breaks
        let formattedMessage = message.replace(/\n\n/g, '<br><br>');
        
        // Replace single newline characters (\n) with a single <br> tag for line breaks
        formattedMessage = formattedMessage.replace(/\n/g, '<br>');
    
        // Create the message container
        const messageContainer = document.createElement("div");
        messageContainer.classList.add("message-container", `${role}-container`);
    
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
            const userIcon =  document.createElement("img");
            userIcon.src = '/static/static/user_icon.png'; // Adjust the path as needed
            userIcon.classList.add("message-icon");
            messageContainer.appendChild(messageElement); // Add the message first
            messageContainer.appendChild(userIcon); // Then add the icon
        }
    
        // Append the entire message container to the chat box
        chatBox.appendChild(messageContainer);
    
        // Scroll to the bottom of the chat box
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    

    function disableSendButton() {
        sendButton.disabled = true;
        sendButton.style.backgroundColor = "#a0a0a0";
    }

    function enableSendButton() {
        sendButton.disabled = false;
        sendButton.style.backgroundColor = "#03005b";
    }
});
