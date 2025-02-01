document.addEventListener('DOMContentLoaded', (event) => {
    const ws = new WebSocket('ws://' + window.location.host + '/ws');
    let isAudioOn = false;
    let currentDMTarget = '-';
    let allPublicMessages = [];
    let readyToStart = false;

    async function submitUsername() {
        const username = prompt("Please enter the name you will use in this conversation simulation:");
        if (username) {
            try {
                const response = await fetch('/set-username', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username: username })
                });

                if (response.ok) {
                    const result = await response.json();
                    alert(result.message);
                    readyToStart = true
                    // localStorage.setItem('Started',readyToStart )
                } else {
                    alert('Error: Unable to start conversation.');
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        else {
            alert("Username cannot be empty.");
        }
    }
    
    console.log('readyToStart', readyToStart)
    console.log('localstorage Started', localStorage.getItem('pendingRollback'))
    if (!readyToStart ){
        if (localStorage.getItem('pendingRollback') === null || JSON.parse(localStorage.getItem('pendingRollback')).applied){
            submitUsername();
            readyToStart = true
        }
    }

    // ================== right column up part ===================
    let characters = [];
    let characterStatusInitialized = false;
    
    function initializeCharacterStatus() {
        fetch('/get-inner-status')
            .then(response => response.json())
            .then(characterData => {
                characters = Object.keys(characterData);
                const statusContainer = document.getElementById('character-status-container');
                statusContainer.innerHTML = '';
    
                if (characters.length === 0) {
                    console.log('No characters received from /get-inner-status');
                    return;
                }
    
                let rowDiv = document.createElement('div');
                rowDiv.className = 'status-row';
                statusContainer.appendChild(rowDiv);
    
                characters.forEach((char, index) => {
                    const statusDiv = document.createElement('div');
                    statusDiv.className = 'character-status';
                    statusDiv.id = `status-${char}`;
    
                    const avatarDiv = document.createElement('div');
                    avatarDiv.className = 'character-avatar';
                    avatarDiv.textContent = char;
                    avatarDiv.addEventListener('click', () => changeDMTarget(char));
    
                    const emotionContainer = document.createElement('div');
                    emotionContainer.className = 'emotion-container';
                    emotionContainer.id = `emotions-${char}`;
    
                    const psystageDiv = document.createElement('div');
                    psystageDiv.className = 'psystage';
                    psystageDiv.id = `psystage-${char}`;
    
                    statusDiv.appendChild(avatarDiv);
                    statusDiv.appendChild(emotionContainer);
                    // statusDiv.appendChild(psystageDiv);
    
                    rowDiv.appendChild(statusDiv);
    
                    if ((index + 1) % 3 === 0 && index < characters.length - 1) {
                        rowDiv = document.createElement('div');
                        rowDiv.className = 'status-row';
                        statusContainer.appendChild(rowDiv);
                    }
                });
    
                updateCharacterInfo(characterData);
                characterStatusInitialized = true;
                console.log('Character status initialized successfully');
            })
            .catch(error => {
                console.error('Error fetching inner status when initiate CharStatus:', error);
                characterStatusInitialized = false;
            });
    }
    
    function updateCharacterStatus() {
        if (!characterStatusInitialized) {
            console.log('Character status not initialized yet. Attempting to initialize...');
            initializeCharacterStatus();
            return;
        }
    
        fetch('/get-inner-status')
            .then(response => response.json())
            .then(characterData => {
                if (Object.keys(characterData).length === 0) {
                    console.log('No character data received from /get-inner-status');
                    return;
                }
                updateCharacterInfo(characterData);
            })
            .catch(error => console.error('Error fetching inner status when upgrade CharStatus:', error));
    }
    
    function updateCharacterInfo(characterData) {
        characters.forEach(char => {
            const charInfo = characterData[char];
    
            if (!charInfo) {
                console.log(`No data for character: ${char}`);
                return;
            }
    
            const statusDiv = document.getElementById(`status-${char}`);
            const emotionContainer = statusDiv.querySelector('.emotion-container');
            const psystageDiv = statusDiv.querySelector('.psystage');
            const avatarDiv = statusDiv.querySelector('.character-avatar');
            
            if (emotionContainer) {
                emotionContainer.innerHTML = '';
                Object.entries(charInfo.emotion).forEach(([emotionName, value]) => {
                    const emotionDiv = document.createElement('div');
                    emotionDiv.className = 'emotion';
                    emotionDiv.innerHTML = `<strong>${emotionName}:</strong> <span>${value}</span>`;
                    emotionContainer.appendChild(emotionDiv);
                });
            }
    
            // if (psystageDiv) {
            //     console.log(`Debug: Psystage for ${char}:`, charInfo.psystage);
            //     if (charInfo.psystage !== undefined) {
            //         psystageDiv.innerHTML = `<strong>Psystage:</strong> ${charInfo.psystage}`;
            //     } else {
            //         psystageDiv.innerHTML = `<strong>Psystage:</strong> Not available`;
            //     }
            // }
    
            // Restore notification dot if there are unread messages
            if (avatarDiv.dataset.hasUnread === 'true') {
                let notificationDot = avatarDiv.querySelector('.notification-dot');
                if (!notificationDot) {
                    notificationDot = document.createElement('div');
                    notificationDot.className = 'notification-dot';
                    avatarDiv.appendChild(notificationDot);
                }
                notificationDot.style.display = 'block';
            }
        });
    }
    
    function updateEmotions(emotions) {
        characters.forEach(char => {
            const emotion = emotions[char]?.emotion;
            if (!emotion) {
                console.log(`No emotion data for character: ${char}`);
                return;
            }
    
            const statusDiv = document.getElementById(`status-${char}`);
            const emotionContainer = statusDiv.querySelector('.emotion-container');
            const avatarDiv = statusDiv.querySelector('.character-avatar');
            
            if (emotionContainer) {
                emotionContainer.innerHTML = '';
                Object.entries(emotion).forEach(([emotionName, value]) => {
                    const emotionDiv = document.createElement('div');
                    emotionDiv.className = 'emotion';
                    emotionDiv.innerHTML = `<strong>${emotionName}:</strong> <span>${value}</span>`;
                    emotionContainer.appendChild(emotionDiv);
                });
            }
    
            // Restore notification dot if there are unread messages
            if (avatarDiv.dataset.hasUnread === 'true') {
                let notificationDot = avatarDiv.querySelector('.notification-dot');
                if (!notificationDot) {
                    notificationDot = document.createElement('div');
                    notificationDot.className = 'notification-dot';
                    avatarDiv.appendChild(notificationDot);
                }
                notificationDot.style.display = 'block';
            }
        });
    }
    
    // Initialize the character status structure
    initializeCharacterStatus();
    
    // Update emotions every 3 seconds
    setInterval(updateCharacterStatus, 3000);

    
    // ================== right column down part ==================
    
    // audio to text
    const micSvg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
        <line x1="12" y1="19" x2="12" y2="23"></line>
        <line x1="8" y1="23" x2="16" y2="23"></line>
    </svg>
    `;    

    const audioInputButtonPB = document.getElementById('audio-input-button-pb');
    const userInputPB = document.getElementById('public-input');

    const audioInputButtonDM = document.getElementById('audio-input-button-dm');
    const userInputDM = document.getElementById('dm-input');

    let isRecording = false;
    let currentRecognizer = null;
    let currentAudioButton = null;
    
    audioInputButtonPB.addEventListener('click', () => handleAudioButtonClick(audioInputButtonPB, userInputPB));
    audioInputButtonDM.addEventListener('click', () => handleAudioButtonClick(audioInputButtonDM, userInputDM));
    
    function handleAudioButtonClick(audioButton, userInput) {
        if (!isRecording) {
            startRecording(audioButton, userInput);
        } else {
            stopRecording();
        }
    }
    
    async function startRecording(audioInputButton, userinput_ele) {
        try {
            isRecording = true;
            audioInputButton.textContent = '⏹️';
            currentAudioButton = audioInputButton;
            const response = await fetch('/get-token');
            const { token, region, language } = await response.json();
            const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(token, region);
            speechConfig.speechRecognitionLanguage = language || "en-US";
    
            const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
            const recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);
    
            let lastRecognitionTime = Date.now();
            let tempText = '';
    
            recognizer.recognizing = (s, e) => {
                console.log(`RECOGNIZING: ${e.result.text}`);
                tempText = e.result.text;
            };
    
            recognizer.recognized = (s, e) => {
                if (e.result.reason == SpeechSDK.ResultReason.RecognizedSpeech) {
                    console.log(`RECOGNIZED: ${e.result.text}`);
                    const currentTime = Date.now();
                    if (currentTime - lastRecognitionTime > 2500) { // 2.5 seconds pause
                        userinput_ele.value += (userinput_ele.value ? ' ' : '') + e.result.text;
                    } else {
                        userinput_ele.value = userinput_ele.value.slice(0, -tempText.length) + e.result.text;
                    }
                    lastRecognitionTime = currentTime;
                    tempText = '';
                }
            };
    
            recognizer.canceled = (s, e) => {
                console.log(`CANCELED: Reason=${e.reason}`);
                if (e.reason == SpeechSDK.CancellationReason.Error) {
                    console.log(`"CANCELED: ErrorCode=${e.errorCode}`);
                    console.log(`"CANCELED: ErrorDetails=${e.errorDetails}`);
                }
                stopRecording();
            };
    
            recognizer.sessionStopped = (s, e) => {
                console.log("\nSession stopped event.");
                stopRecording();
            };
    
            console.log("Starting continuous recognition");
            recognizer.startContinuousRecognitionAsync();
    
            currentRecognizer = recognizer;
        } catch (error) {
            console.error('Error starting recording:', error);
            stopRecording();
        }
    }
    
    function stopRecording() {
        if (currentRecognizer) {
            currentRecognizer.stopContinuousRecognitionAsync(
                () => {
                    currentRecognizer.close();
                    currentRecognizer = null;
                    isRecording = false;
                    if (currentAudioButton) {
                        currentAudioButton.innerHTML = micSvg;
                        currentAudioButton = null;
                    }
                },
                (err) => {
                    console.error(err);
                    isRecording = false;
                    if (currentAudioButton) {
                        currentAudioButton.innerHTML = micSvg;
                        currentAudioButton = null;
                    }
                }
            );
        } else {
            isRecording = false;
            if (currentAudioButton) {
                currentAudioButton.innerHTML = micSvg;
                currentAudioButton = null;
            }
        }
    }
    function changeDMTarget(target) {
        currentDMTarget = target;
        document.getElementById('dm-target').textContent = target;
        document.getElementById('dm-chat').innerHTML = ''; // Clear previous DM chat
        console.log(`Changed DM target to ${target}`);
        loadChatHistory(target);
        clearNotificationDot(target);
    }

    async function sendPublicMessage() {
        const input = document.getElementById('public-input');
        const message = input.value.trim();
        if (message) {
            addMessageToChat('public-chat', 'You', message);
            input.value = '';
            // Send public message to server
            try {
                const serverResponse = await sendPMToServer(message);
            } catch (error) {
                console.error('Error sending public message:', error);
            }
            // // resume/start public chat
            // if (conversationState != 'started'){
            //     await changeConversationState('started', '/start-conversation', 'Conversation started successfully', 'Suspend Public Chat');
            // }
        }
    }

    function sendDMMessage() {
        const input = document.getElementById('dm-input');
        const message = input.value.trim();
        if (message) {
            addMessageToChat('dm-chat', 'You', message);
            input.value = '';
            // Send DM to server
            sendDMToServer(currentDMTarget, message);
        }
    }

    function addMessageToChat(chatId, role, content, speechFile, timestamp) {
        if ( chatId == 'public-chat' || (chatId == 'dm-chat' && role == 'You') || (chatId == 'dm-chat' && role != 'You' && role == currentDMTarget)){

            const chatContainer = document.getElementById(chatId);
            const chatBubble = document.createElement('div');
            chatBubble.dataset.timestamp = timestamp;
            chatBubble.className = 'chat-bubble';
            chatBubble.innerHTML = `
                <div class="avatar">${role[0]}</div>
                <div class="message-content">
                    <div class="name">${role}</div>
                    <div>${content}</div>
                </div>
            `;
            chatContainer.appendChild(chatBubble);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            if (speechFile && isAudioOn) {
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
                console.log('Audio not played. speechFile:', speechFile, 'audioEnabled:', isAudioOn);
            }
        }
        else{
            updateNotificationDot(role)
        }
    }

    function updateNotificationDot(character) {
        const avatarDivs = document.querySelectorAll('.character-avatar');
        for (let avatarDiv of avatarDivs) {
            if (avatarDiv.textContent.trim() === character) {
                let notificationDot = avatarDiv.querySelector('.notification-dot');
                if (!notificationDot) {
                    notificationDot = document.createElement('div');
                    notificationDot.className = 'notification-dot';
                    avatarDiv.appendChild(notificationDot);
                }
                notificationDot.style.display = 'block';
                avatarDiv.dataset.hasUnread = 'true';
                break;
            }
        }
    }
    
    let notificationSound = new Audio('message_notification.wav');

    function updateNotificationDot(character) {
        const avatarDivs = document.querySelectorAll('.character-avatar');
        for (let avatarDiv of avatarDivs) {
            if (avatarDiv.textContent.trim() === character) {
                let notificationDot = avatarDiv.querySelector('.notification-dot');
                if (!notificationDot) {
                    notificationDot = document.createElement('div');
                    notificationDot.className = 'notification-dot';
                    avatarDiv.appendChild(notificationDot);
                }
                notificationDot.style.display = 'block';
                avatarDiv.dataset.hasUnread = 'true';
                
                // Play notification sound
                playNotificationSound();
                
                break;
            }
        }
    }

function playNotificationSound() {
    // Check if the browser supports the Audio API
    if (typeof Audio !== "undefined") {
        try {
            notificationSound.play().catch(error => {
                console.error('Error playing notification sound:', error);
            });
        } catch (error) {
            console.error('Error playing notification sound:', error);
        }
    } else {
        console.warn('Audio is not supported in this browser');
    }
}
    
    function clearNotificationDot(character) {
        const avatarDivs = document.querySelectorAll('.character-avatar');
        for (let avatarDiv of avatarDivs) {
            if (avatarDiv.textContent.trim() === character) {
                const notificationDot = avatarDiv.querySelector('.notification-dot');
                if (notificationDot) {
                    notificationDot.style.display = 'none';
                }
                avatarDiv.dataset.hasUnread = 'false';
                break;
            }
        }
    }

    function loadChatHistory(target) {
        fetch('/dm-history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ recipient: target }),
        })
        .then(response => response.json())
        .then(data => {
            const chatContainer = document.getElementById('dm-chat');
            chatContainer.innerHTML = ''; // Clear existing messages
            console.log('Loaded chat history:', data);
            data.forEach(msg => {
                addMessageToChat('dm-chat', msg.role, msg.content);
            });
        })
        .catch(error => {
            console.error('Error loading chat history:', error);
        });
    }
    
    async function sendPMToServer(message) {
        try {
            const response = await fetch('/public-input', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ input: message }),
            });
    
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
    
            const data = await response.json();
            return data.response;
        } catch (error) {
            console.error('Error sending message to server:', error);
            throw error;
        }
    }

    // Simulated server function to receive DM
    async function sendDMToServer(currentDMTarget, message) {
        try {
            const response = await fetch('/dm-input', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ recipient: currentDMTarget, message: message }),
            });
    
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
    
        } catch (error) {
            console.error('Error sending DM to server:', error);
            throw error;
        }
    }

    // Handle incoming messages from the server 
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        addMessageToChat(msg.channel, msg.role, msg.content, msg.speechFile, msg.timestamp);
    };

    checkAndApplyRollback();

    // Start conversation button
    const startConversationButton = document.getElementById('start-conversation');
    let conversationState = 'idle'; // possible states: 'idle', 'started', 'suspended'

    // Function to handle conversation state changes
    async function changeConversationState(newState, endpoint, successMessage, buttonText) {
        try {
            const response = await fetch(endpoint, { method: 'POST' });
            if (response.ok) {
                console.log(successMessage);
                startConversationButton.textContent = buttonText;
                conversationState = newState;
            } else {
                console.error(`Failed to ${newState} conversation`);
            }
        } catch (error) {
            console.error(`Error ${newState} conversation:`, error);
        }
    }

    // Attach event listener to the button
    startConversationButton.addEventListener('click', async () => {
        switch (conversationState) {
            case 'idle':
                await changeConversationState('started', '/start-conversation', 'Conversation started successfully', 'Suspend Public Chat');
                break;
            case 'started':
                await changeConversationState('suspended', '/suspend-conversation', 'Conversation suspended successfully', 'Resume Public Chat');
                break;
            case 'suspended':
                await changeConversationState('started', '/resume-conversation', 'Conversation resumed successfully', 'Suspend Public Chat');
                break;
        }
    });


    // Check for rollback timestamp 
    function checkAndApplyRollback() {
        try {
            const pendingRollbackJSON = localStorage.getItem('pendingRollback');
            if (pendingRollbackJSON) {
                const pendingRollback = JSON.parse(pendingRollbackJSON);
                if (!pendingRollback.applied) {
                    publicMessages(pendingRollback.timestamp);
                    // Mark as applied
                    pendingRollback.applied = true;
                    localStorage.setItem('pendingRollback', JSON.stringify(pendingRollback));
                    console.log(`Applied rollback to ${new Date(pendingRollback.timestamp).toLocaleString()}`);
                }
            }
        } catch (error) {
            console.error('Could not access localStorage:', error);
            // Fallback logic, e.g., using sessionStorage or cookies
        }
    }
    

    async function publicMessages(timestamp) {
        // Fetch public messages from the server
        const publicChat = document.getElementById('public-chat');
    
        // Clear the chat container
        publicChat.innerHTML = '';
    
        // Fetch messages
        const response = await fetch('/public-messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ timestamp: timestamp }),
        });
    
        // Ensure the response is in JSON format
        if (response.ok) {
            allPublicMessages = await response.json();
    
            // Re-add filtered messages
            allPublicMessages.forEach(msg => {
                addMessageToChat('public-chat', msg.role, msg.content, msg.speechFile, msg.timestamp);
            });
    
            console.log(`Rolled back to ${new Date(timestamp).toLocaleString()}`);
        } else {
            console.error('Failed to fetch messages:', response.statusText);
        }
    }
    

    // Add event listener for Enter key in input field
    document.getElementById('public-input').addEventListener('keydown', async function(event) {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent the default action (form submission or line break)
            await sendPublicMessage();
        }
    });
    document.getElementById('dm-input').addEventListener('keydown', async function(event) {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent the default action (form submission or line break)
            await sendDMMessage();
        }
    });

    window.sendDMMessage = sendDMMessage;
    window.sendPublicMessage = sendPublicMessage;

    // // Audio toggle functionality
    const audioToggleButton = document.getElementById('audio-toggle');
    audioToggleButton.addEventListener('click', function() {
        // Toggle the audio state
        isAudioOn = !isAudioOn;

        // Update the button text based on the audio state
        if (isAudioOn) {
            audioToggleButton.textContent = 'Audio on';
        } else {
            audioToggleButton.textContent = 'Audio off';
        }

        // Optionally, you can add logic here to enable/disable audio functionality
        console.log(`Audio is now ${isAudioOn ? 'on' : 'off'}`);
    });

    // Analyse user behavior
    const analyseButton = document.getElementById('user-analyse');
    analyseButton.addEventListener('click', async function() {
        analyseButton.textContent = 'Analyzing...';

        try {
            const response = await fetch('/user-analyse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}),
            });
    
            if (response.ok) {
                const chatHistories = await response.json();
                // Store the chatHistories in localStorage
                localStorage.setItem('chatHistories', JSON.stringify(chatHistories));
                
                // Navigate to analyse.html
                window.location.href = '/analyse';

            } else {
                console.error('Error in analysis request:', response.status, response.statusText);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
});

function isURL(str) {
    const pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
        '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
    return !!pattern.test(str);
}
