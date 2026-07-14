(function () {
    const players = [
        {
            audio: document.getElementById("polotuAudio"),
            playToggle: document.getElementById("audioPlayToggle"),
            muteToggle: document.getElementById("audioMuteToggle"),
        },
        {
            audio: document.getElementById("polotuAudioMobile"),
            playToggle: document.getElementById("audioPlayToggleMobile"),
            muteToggle: document.getElementById("audioMuteToggleMobile"),
        },
    ].filter(function (player) {
        return player.audio && player.playToggle && player.muteToggle;
    });

    function setIcon(button, html) {
        const icon = button.querySelector("span");
        if (icon) {
            icon.innerHTML = html;
        } else {
            button.innerHTML = '<span aria-hidden="true">' + html + "</span>";
        }
    }

    function setButtonState(player) {
        const isPlaying = !player.audio.paused;

        setIcon(player.playToggle, isPlaying ? "&#10074;&#10074;" : "&#9658;");
        player.playToggle.setAttribute("aria-label", isPlaying ? "Pause polotu" : "Play polotu");
        player.playToggle.setAttribute("aria-pressed", String(isPlaying));
        player.playToggle.setAttribute("title", isPlaying ? "Pause polotu" : "Play polotu");

        setIcon(player.muteToggle, player.audio.muted ? "&#128263;" : "&#128266;");
        player.muteToggle.setAttribute("aria-label", player.audio.muted ? "Unmute polotu" : "Mute polotu");
        player.muteToggle.setAttribute("aria-pressed", String(player.audio.muted));
        player.muteToggle.setAttribute("title", player.audio.muted ? "Unmute polotu" : "Mute polotu");
    }

    function pauseOtherPlayers(activePlayer) {
        players.forEach(function (player) {
            if (player !== activePlayer && !player.audio.paused) {
                player.audio.pause();
                setButtonState(player);
            }
        });
    }

    async function playAudio(player) {
        try {
            pauseOtherPlayers(player);
            player.audio.volume = 0.72;
            player.audio.load();
            await player.audio.play();
        } catch (error) {
            // Browser autoplay policies and missing files reject play(); keep controls truthful.
            if (window.console) {
                console.warn("Polotu audio could not be played.", error);
            }
        } finally {
            setButtonState(player);
        }
    }

    function wirePlayer(player) {
        player.playToggle.addEventListener(
            "click",
            function (event) {
                event.preventDefault();
                event.stopImmediatePropagation();

                if (player.audio.paused) {
                    playAudio(player);
                } else {
                    player.audio.pause();
                    setButtonState(player);
                }
            },
            true
        );

        player.muteToggle.addEventListener(
            "click",
            function (event) {
                event.preventDefault();
                event.stopImmediatePropagation();

                player.audio.muted = !player.audio.muted;
                setButtonState(player);
            },
            true
        );

        player.audio.addEventListener("play", function () {
            pauseOtherPlayers(player);
            setButtonState(player);
        });
        player.audio.addEventListener("pause", function () {
            setButtonState(player);
        });
        player.audio.addEventListener("volumechange", function () {
            setButtonState(player);
        });
        player.audio.addEventListener("error", function () {
            setButtonState(player);
        });

        setButtonState(player);
    }

    players.forEach(wirePlayer);
})();
