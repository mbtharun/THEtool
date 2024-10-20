const chatbox = document.getElementById('chatbox');
const sendButton = document.querySelector('.send-button');
const inputField = document.getElementById('user-input');

sendButton.addEventListener('click', () => {
    const userMessage = inputField.value.trim();
    if (userMessage) {
        // Append user message
        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'message message-user';
        userMessageDiv.textContent = userMessage;
        chatbox.appendChild(userMessageDiv);

        // Clear input
        inputField.value = '';

        // Send request to the server
        fetch('/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: userMessage })
        })
        .then(response => response.json())
        .then(data => {
            const botMessageDiv = document.createElement('div');
            botMessageDiv.className = 'message message-bot';
            botMessageDiv.textContent = "Bot: " + data.response; // Show bot response
            chatbox.appendChild(botMessageDiv);
            chatbox.scrollTop = chatbox.scrollHeight; // Scroll to bottom
        })
        .catch(error => {
            console.error('Error:', error);
            const errorDiv = document.createElement('div');
            errorDiv.className = 'message message-bot';
            errorDiv.textContent = "Bot: Sorry, there was an error processing your request.";
            chatbox.appendChild(errorDiv);
            chatbox.scrollTop = chatbox.scrollHeight; // Scroll to bottom
        });
    }
});

// Allow sending message with Enter key
inputField.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        sendButton.click(); // Trigger the send button click
    }
});
