document.addEventListener("DOMContentLoaded", function () {
    let currentAudioElement = null;

    // Function to stop the current audio
    window.stopCurrentAudio = function() {
        if (currentAudioElement) {
            console.log(`stopCurrentAudio: Attempting to stop: ${currentAudioElement.id}`);
        } else {
            console.log("stopCurrentAudio: currentAudioElement is null or undefined.");
        }

        if (currentAudioElement && !currentAudioElement.paused) {
            console.log(`stopCurrentAudio: Stopping current audio: ${currentAudioElement.id}`);
            try {
                currentAudioElement.pause();
                currentAudioElement.currentTime = 0;
                currentAudioElement = null;  // Reset the current audio element after stopping
            } catch (err) {
                console.error("stopCurrentAudio: Error stopping audio:", err);
            }
        } else {
            console.log("stopCurrentAudio: No current audio to stop.");
        }
    };

    window.playNewAudio = function(audioElement) {
        if (audioElement) {
            console.log(`playNewAudio: New audio element detected: ${audioElement.id}`);
            stopCurrentAudio();  // Stop any previous audio
    
            // Set the current audio element before playback begins
            currentAudioElement = audioElement;
            setTimeout(() => {
                console.log(`playNewAudio: Playing audio after delay: ${audioElement.id}`);
                audioElement.play().catch(function (error) {
                    console.error("Autoplay failed, triggering manual play:", error);
                    audioElement.play(); // Attempt manual play
                });
                audioElement.addEventListener('ended', function () {
                    console.log(`playNewAudio: Audio finished: ${audioElement.id}`);
                    currentAudioElement = null;  // Clear the current audio reference after playback ends
                });
            }, 300);  // Delay to ensure proper timing
        }
    };
    

    // Play the first audio element when the page loads (optional if you need)
    const firstAudioElement = document.querySelector('audio');
    if (firstAudioElement) {
        console.log(`Initial audio found: ${firstAudioElement.id}`);
        playNewAudio(firstAudioElement);  // Play the audio immediately
    } else {
        console.warn("No initial audio element found.");
    }
});
