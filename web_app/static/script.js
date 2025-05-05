document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const portLoading = document.getElementById('port-loading');
    const noPorts = document.getElementById('no-ports');
    const countdownForm = document.getElementById('countdown-form');
    const portSelect = document.getElementById('port-select');
    const secondsInput = document.getElementById('seconds-input');
    const baudrateInput = document.getElementById('baudrate-input');
    const startButton = document.getElementById('start-button');
    const statusContainer = document.getElementById('status-container');
    const statusMessage = document.getElementById('status-message');
    
    // Load available ports when the page loads
    loadPorts();
    
    // Set up the form submission
    countdownForm.addEventListener('submit', function(event) {
        event.preventDefault();
        startCountdown();
    });
    
    // Function to load available ports
    function loadPorts() {
        fetch('/api/ports')
            .then(response => response.json())
            .then(data => {
                portLoading.style.display = 'none';
                
                if (data.success && data.ports.length > 0) {
                    // Populate the port select dropdown
                    data.ports.forEach(port => {
                        const option = document.createElement('option');
                        option.value = port.index;
                        option.textContent = `${port.device} - ${port.description}`;
                        portSelect.appendChild(option);
                    });
                    
                    // Show the form
                    countdownForm.style.display = 'block';
                } else {
                    // Show the no ports message
                    noPorts.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error loading ports:', error);
                portLoading.style.display = 'none';
                showStatus('error', 'Error loading ports. Please refresh the page.');
            });
    }
    
    // Function to start the countdown
    function startCountdown() {
        // Get form values
        const portIndex = portSelect.value;
        const seconds = secondsInput.value;
        const baudrate = baudrateInput.value;
        
        // Disable the form
        setFormEnabled(false);
        
        // Show loading status
        showStatus('running', 'Starting countdown...');
        
        // Send the request to start the countdown
        fetch('/api/countdown', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                port_index: portIndex,
                seconds: seconds,
                baudrate: baudrate
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus('running', `Countdown running for ${seconds} seconds...`);
                // Start polling for status
                pollStatus();
            } else {
                showStatus('error', `Error: ${data.error}`);
                setFormEnabled(true);
            }
        })
        .catch(error => {
            console.error('Error starting countdown:', error);
            showStatus('error', 'Error starting countdown. Please try again.');
            setFormEnabled(true);
        });
    }
    
    // Function to poll for status
    function pollStatus() {
        const statusInterval = setInterval(() => {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (data.status === 'idle' && !data.running) {
                            // Countdown is complete
                            clearInterval(statusInterval);
                            showStatus('success', 'Countdown complete!');
                            setFormEnabled(true);
                        } else {
                            // Countdown is still running
                            showStatus('running', 'Countdown in progress...');
                        }
                    } else {
                        clearInterval(statusInterval);
                        showStatus('error', 'Error checking status.');
                        setFormEnabled(true);
                    }
                })
                .catch(error => {
                    console.error('Error polling status:', error);
                    clearInterval(statusInterval);
                    showStatus('error', 'Error checking status.');
                    setFormEnabled(true);
                });
        }, 1000);
    }
    
    // Function to show status messages
    function showStatus(type, message) {
        statusContainer.style.display = 'block';
        statusContainer.className = '';
        statusContainer.classList.add(type);
        statusMessage.textContent = message;
    }
    
    // Function to enable/disable the form
    function setFormEnabled(enabled) {
        portSelect.disabled = !enabled;
        secondsInput.disabled = !enabled;
        baudrateInput.disabled = !enabled;
        startButton.disabled = !enabled;
    }
});
