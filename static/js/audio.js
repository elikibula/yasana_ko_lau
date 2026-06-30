(function () {
    const audio = document.getElementById("polotuAudio");
    const playToggle = document.getElementById("audioPlayToggle");
    const muteToggle = document.getElementById("audioMuteToggle");

    if (!audio || !playToggle || !muteToggle) {
        return;
    }

    const playIcon = playToggle.querySelector("span");
    const muteIcon = muteToggle.querySelector("span");

    function setButtonState() {
        const isPlaying = !audio.paused;

        if (playIcon) playIcon.innerHTML = isPlaying ? "&#10074;&#10074;" : "&#9658;";
        playToggle.setAttribute("aria-label", isPlaying ? "Pause polotu" : "Play polotu");
        playToggle.setAttribute("aria-pressed", String(isPlaying));
        playToggle.setAttribute("title", isPlaying ? "Pause polotu" : "Play polotu");

        if (muteIcon) muteIcon.innerHTML = audio.muted ? "&#128263;" : "&#128266;";
        muteToggle.setAttribute("aria-label", audio.muted ? "Unmute polotu" : "Mute polotu");
        muteToggle.setAttribute("aria-pressed", String(audio.muted));
        muteToggle.setAttribute("title", audio.muted ? "Unmute polotu" : "Mute polotu");
    }

    async function startAudio() {
        try {
            audio.volume = 0.72;
            await audio.play();
        } catch (error) {
            setButtonState();
        }
    }

    playToggle.addEventListener("click", async function () {
        if (audio.paused) {
            await startAudio();
        } else {
            audio.pause();
        }
        setButtonState();
    });

    muteToggle.addEventListener("click", function () {
        audio.muted = !audio.muted;
        setButtonState();
    });

    audio.addEventListener("play", setButtonState);
    audio.addEventListener("pause", setButtonState);
    audio.addEventListener("volumechange", setButtonState);
    setButtonState();
})();
