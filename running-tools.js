(() => {
    const lapDistances = [100, 200, 300, 400, 500, 600, 800, 1000, 1200, 1500, 1800, 2000, 3000];
    // Pace multipliers are centred on lactate-threshold pace and make the
    // short-to-long trade-off explicit through the selected strength profile.
    const raceDistances = [
        // label, km, neutral pace ratio, lactate-threshold influence, VO₂max influence, speed-strength influence
        ["400 m", 0.4, 0.63, 0.08, 0.08, 0.12],
        ["800 m", 0.8, 0.69, 0.22, 0.18, 0.09],
        ["1500 m", 1.5, 0.76, 0.48, 0.35, 0.08],
        ["3000 m", 3, 0.83, 0.8, 1, 0.005],
        ["5 km", 5, 0.88, 0.95, 1, -0.015],
        ["10 km", 10, 0.94, 1, 0.95, -0.025],
        ["21.1 km", 21.0975, 1, 1, 0.6, -0.04],
        ["marathon", 42.195, 1.05, 1, 0.3, -0.06],
    ];

    const formatTime = (seconds) => {
        const rounded = Math.max(0, Math.round(seconds));
        const minutes = Math.floor(rounded / 60);
        return `${minutes}:${String(rounded % 60).padStart(2, "0")}`;
    };

    const formatRaceTime = (seconds) => seconds >= 3600
        ? `${Math.floor(seconds / 3600)}:${String(Math.floor((seconds % 3600) / 60)).padStart(2, "0")}:${String(Math.round(seconds % 60)).padStart(2, "0")}`
        : formatTime(seconds);

    const parseTime = (value) => {
        const parts = String(value).trim().split(":").map(Number);
        if (!parts.length || parts.some((part) => !Number.isFinite(part) || part < 0)) return null;
        if (parts.length === 1) return parts[0];
        if (parts.length === 2 && parts[1] < 60) return parts[0] * 60 + parts[1];
        if (parts.length === 3 && parts[1] < 60 && parts[2] < 60) return parts[0] * 3600 + parts[1] * 60 + parts[2];
        return null;
    };

    const paceSeconds = document.getElementById("pace-seconds");
    const paceValue = document.getElementById("pace-value");
    const milePace = document.getElementById("mile-pace");
    const paceResults = document.getElementById("pace-results");
    const speedResult = document.getElementById("speed-result");
    const finishDistance = document.getElementById("finish-distance");
    const finishTime = document.getElementById("finish-time");
    const updatePace = () => {
        const pace = Number(paceSeconds.value);
        paceValue.value = `${formatTime(pace)} min/km`;
        milePace.textContent = `${formatTime(pace * 1.609344)} min/mi`;
        speedResult.textContent = `${(3600 / pace).toFixed(1)} km/h`;
        const distance = Number(finishDistance.value);
        finishTime.value = distance > 0 ? formatRaceTime(pace * distance / 1000) : "—";
        paceResults.innerHTML = lapDistances.map((distance) => `<tr><td>${distance}</td><td><input class="lap-time-input" data-distance="${distance}" inputmode="numeric" aria-label="${distance} metre lap time" value="${formatTime(pace * distance / 1000)}"></td></tr>`).join("");
    };

    paceSeconds.addEventListener("input", updatePace);
    finishDistance.addEventListener("input", updatePace);
    finishTime.addEventListener("change", () => {
        const time = parseTime(finishTime.value);
        const distance = Number(finishDistance.value);
        if (!time || !distance) {
            updatePace();
            return;
        }
        paceSeconds.value = String(Math.min(Number(paceSeconds.max), Math.max(Number(paceSeconds.min), Math.round(time * 1000 / distance))));
        updatePace();
    });
    paceResults.addEventListener("change", (event) => {
        if (!event.target.matches(".lap-time-input")) return;
        const time = parseTime(event.target.value);
        const distance = Number(event.target.dataset.distance);
        if (!time || !distance) {
            updatePace();
            return;
        }
        paceSeconds.value = String(Math.min(Number(paceSeconds.max), Math.max(Number(paceSeconds.min), Math.round(time * 1000 / distance))));
        updatePace();
    });

    const vo2max = document.getElementById("vo2max");
    const threshold = document.getElementById("threshold");
    const vo2maxValue = document.getElementById("vo2max-value");
    const thresholdValue = document.getElementById("threshold-value");
    const performanceResults = document.getElementById("performance-results");
    const runnerStrength = document.getElementById("runner-strength");
    const runnerStrengthValue = document.getElementById("runner-strength-value");
    const strengthNames = ["speed", "speed leaning", "speed / neutral", "neutral", "neutral / endurance", "endurance leaning", "endurance"];

    const thresholdFor = (vo2, strength) => Math.round((215 * 62) / vo2 + (3 - strength) * 4);
    const vo2For = (thresholdPace, strength) => (215 * 62) / (thresholdPace - (3 - strength) * 4);

    const raceTime = (distance, ratio, thresholdInfluence, vo2Influence, strengthInfluence, vo2, thresholdPace, strength) => {
        const referenceThreshold = thresholdFor(62, strength);
        const effectiveThreshold = thresholdPace * thresholdInfluence + referenceThreshold * (1 - thresholdInfluence);
        const vo2Factor = 1 - (vo2 - 62) * 0.004 * vo2Influence;
        const strengthFactor = 1 + ((strength - 3) / 3) * strengthInfluence;
        return effectiveThreshold * distance * ratio * vo2Factor * strengthFactor;
    };

    const renderPerformance = () => {
        const vo2 = Number(vo2max.value);
        const thresholdPace = Number(threshold.value);
        const strength = Number(runnerStrength.value);
        vo2maxValue.value = vo2 % 1 === 0 ? String(vo2) : vo2.toFixed(1);
        thresholdValue.value = `${formatTime(thresholdPace)} min/km`;
        runnerStrengthValue.value = strengthNames[strength];
        performanceResults.innerHTML = raceDistances.map(([label, distance, ratio, thresholdInfluence, vo2Influence, strengthInfluence]) => {
            const totalSeconds = raceTime(distance, ratio, thresholdInfluence, vo2Influence, strengthInfluence, vo2, thresholdPace, strength);
            return `<tr><td>${label}</td><td><input class="prediction-input" data-distance="${distance}" data-ratio="${ratio}" data-threshold-influence="${thresholdInfluence}" data-vo2-influence="${vo2Influence}" data-strength-influence="${strengthInfluence}" inputmode="numeric" aria-label="${label} prediction" value="${formatRaceTime(totalSeconds)}"></td></tr>`;
        }).join("");
    };

    const updateFromVo2 = () => {
        threshold.value = String(Math.min(Number(threshold.max), Math.max(Number(threshold.min), thresholdFor(Number(vo2max.value), Number(runnerStrength.value)))));
        renderPerformance();
    };
    const updateFromThreshold = () => {
        vo2max.value = String(Math.min(Number(vo2max.max), Math.max(Number(vo2max.min), vo2For(Number(threshold.value), Number(runnerStrength.value)))));
        renderPerformance();
    };
    vo2max.addEventListener("input", updateFromVo2);
    threshold.addEventListener("input", updateFromThreshold);
    runnerStrength.addEventListener("input", updateFromVo2);
    performanceResults.addEventListener("change", (event) => {
        if (!event.target.matches(".prediction-input")) return;
        const time = parseTime(event.target.value);
        const distance = Number(event.target.dataset.distance);
        const ratio = Number(event.target.dataset.ratio);
        const thresholdInfluence = Number(event.target.dataset.thresholdInfluence);
        const vo2Influence = Number(event.target.dataset.vo2Influence);
        const strengthInfluence = Number(event.target.dataset.strengthInfluence);
        const strength = Number(runnerStrength.value);
        if (!time || !distance || !ratio || !Number.isFinite(thresholdInfluence) || !Number.isFinite(vo2Influence) || !Number.isFinite(strengthInfluence)) {
            renderPerformance();
            return;
        }
        let low = Number(vo2max.min);
        let high = Number(vo2max.max);
        for (let iteration = 0; iteration < 32; iteration += 1) {
            const middle = (low + high) / 2;
            const predicted = raceTime(distance, ratio, thresholdInfluence, vo2Influence, strengthInfluence, middle, thresholdFor(middle, strength), strength);
            if (predicted > time) low = middle;
            else high = middle;
        }
        vo2max.value = String((low + high) / 2);
        updateFromVo2();
    });

    document.querySelectorAll(".tool-tab").forEach((button) => {
        button.addEventListener("click", () => {
            const selected = button.dataset.tool;
            document.querySelectorAll(".tool-tab").forEach((item) => {
                const active = item === button;
                item.classList.toggle("active", active);
                item.setAttribute("aria-selected", String(active));
            });
            document.getElementById("pace-panel").hidden = selected !== "pace";
            document.getElementById("performance-panel").hidden = selected !== "performance";
        });
    });

    let installPrompt;
    const installButton = document.getElementById("install-app");
    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        installPrompt = event;
        installButton.hidden = false;
    });
    installButton?.addEventListener("click", async () => {
        if (!installPrompt) return;
        installPrompt.prompt();
        await installPrompt.userChoice;
        installPrompt = undefined;
        installButton.hidden = true;
    });

    if ("serviceWorker" in navigator) {
        window.addEventListener("load", () => navigator.serviceWorker.register("/service-worker.js"));
    }

    updatePace();
    renderPerformance();
})();
