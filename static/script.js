document.addEventListener('DOMContentLoaded', (event) => {
    console.log('DOM fully loaded and parsed');

    const chatContainer = document.querySelector('.chat-container');
    const ws = new WebSocket('ws://' + window.location.host + '/ws');
    let audioEnabled = false;

    // audio to text
    const audioInputButton = document.getElementById('audio-input-button');
    let isRecording = false;

    audioInputButton.addEventListener('click', () => {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    });

    async function startRecording() {
        try {
            isRecording = true;
            audioInputButton.textContent = '⏹️';
            const response = await fetch('/get-token');
            const { token, region } = await response.json();
            console.log('Token:', token, 'Region:', region); 
            const speechConfig = SpeechSDK.SpeechConfig.fromAuthorizationToken(token, region);
            speechConfig.speechRecognitionLanguage = 'en-US';
    
            const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
            recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);
    
            recognizer.recognizeOnceAsync(
                result => {
                    if (result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
                        document.getElementById('user-input').value = result.text;
                    }
                    stopRecording(recognizer);
                },
                error => {
                    console.error(error);
                    stopRecording(recognizer);
                }
            );
        } catch (error) {
            console.error('Error starting recording:', error);
            stopRecording();
        }
    }
    
    function stopRecording(recognizer) {
        if (recognizer) {
            recognizer.close();
        }
        isRecording = false;
        audioInputButton.textContent = '🎤';
    }

    // Create a chat bubble
    function createMessageBubble(role, content, speechFile) {
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'chat-bubble';
        
        const avatar = document.createElement('img');
        avatar.className = 'avatar';
        avatar.src = `https://api.dicebear.com/6.x/initials/svg?seed=${role}`;
        avatar.alt = role;
    
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
    
        const name = document.createElement('div');
        name.className = 'name';
        name.textContent = role;
    
        const text = document.createElement('div');
        text.textContent = content;
    
        messageContent.appendChild(name);
        messageContent.appendChild(text);
    
        bubbleDiv.appendChild(avatar);
        bubbleDiv.appendChild(messageContent);
    
        if (speechFile && audioEnabled) {
            const audio = new Audio();
            if (isURL(speechFile)) {
                // For online URLs
                audio.crossOrigin = "anonymous";
                audio.src = speechFile;
            } else {
                // For local files
                audio.src = speechFile;
            }
            audio.play().then(() => {
                console.log('Audio played successfully');
            }).catch((error) => {
                console.error('Error playing audio:', error);
            });
        }
        else {
            console.log('Audio not played. speechFile:', speechFile, 'audioEnabled:', audioEnabled);
        }
        return bubbleDiv;
    }
    // Handle incoming messages from the server
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        const messageBubble = createMessageBubble( msg.role, msg.content, msg.speechFile);
        chatContainer.appendChild(messageBubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    };

    // Audio toggle functionality
    const audioToggle = document.createElement('button');
    audioToggle.textContent = 'Audio: Off';
    audioToggle.className = 'audio-toggle';
    document.body.appendChild(audioToggle);

    audioToggle.addEventListener('click', () => {
        audioEnabled = !audioEnabled;
        audioToggle.textContent = audioEnabled ? 'Audio: On' : 'Audio: Off';
    });

    // Send user input to the server via HTTP POST
    const handleInputSubmit = async (event) => {
        event.preventDefault();
        const userInput = document.getElementById('user-input').value;
        // Send input to server via HTTP POST
        const response = await fetch('/input', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ input: userInput }),
        });
        
        // Display user input
        const userBubble = createMessageBubble('You', userInput);
        chatContainer.appendChild(userBubble);

        chatContainer.scrollTop = chatContainer.scrollHeight;
        document.getElementById('user-input').value = ''; // Clear input field
    };
   
    
    // Start conversation button
    const startConversationButton = document.getElementById('start-conversation');
    let conversationState = 'idle'; // possible states: 'idle', 'started', 'suspended'

    // Function to start the conversation
    async function startConversation() {
        try {
            const response = await fetch('/start-conversation', { method: 'POST' });
            if (response.ok) {
                console.log('Conversation started successfully');
                // startConversationButton.disabled = true;
                startConversationButton.textContent = 'Suspend Conversation';
                conversationState = 'started';
            } else {
                console.error('Failed to start conversation');
            }
        } catch (error) {
            console.error('Error starting conversation:', error);
        }
    }

    // Function to suspend the conversation
    async function suspendConversation() {
        try {
            const response = await fetch('/suspend-conversation', { method: 'POST' });
            if (response.ok) {
                console.log('Conversation suspended successfully');
                // startConversationButton.disabled = false;
                startConversationButton.textContent = 'Resume Conversation';
                conversationState = 'suspended';
            } else {
                console.error('Failed to suspend conversation');
            }
        } catch (error) {
            console.error('Error suspending conversation:', error);
        }
    }

    // Function to resume the conversation
    async function resumeConversation() {
        try {
            const response = await fetch('/resume-conversation', { method: 'POST' });
            if (response.ok) {
                console.log('Conversation resumed successfully');
                // startConversationButton.disabled = true;
                startConversationButton.textContent = 'Suspend Conversation';
                conversationState = 'started';
            } else {
                console.error('Failed to resume conversation');
            }
        } catch (error) {
            console.error('Error resuming conversation:', error);
        }
    }

    // Attach event listener to the button
    startConversationButton.addEventListener('click', async () => {
        switch (conversationState) {
            case 'idle':
                await startConversation();
                break;
            case 'started':
                await suspendConversation();
                break;
            case 'suspended':
                await resumeConversation();
                break;
        }
    });

    // Initialize event listeners
    const init = () => {
        const inputForm = document.getElementById('input-form');
        inputForm.addEventListener('submit', handleInputSubmit);
    };

    init();
});


function fetchAndPlayAudio(url) {
    fetch(url)
        .then(response => response.blob())
        .then(blob => {
            const audioUrl = URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);
            return audio.play();
        })
        .then(() => {
            console.log('Audio played successfully using fetch');
        })
        .catch((error) => {
            console.error('Error playing audio using fetch:', error);
        });
}

function isURL(str) {
    const pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
        '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
    return !!pattern.test(str);
}
