class FlappyBird {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Game state
        this.gameState = 'start'; // 'start', 'playing', 'gameOver', 'paused'
        this.score = 0;
        this.bestScore = localStorage.getItem('flappyBirdBestScore') || 0;
        this.isPaused = false;
        this.difficulty = 1;
        
        // Sound system
        this.soundEnabled = localStorage.getItem('flappyBirdSound') !== 'false';
        this.sounds = {
            flap: this.createAudioContext() ? this.createSound(200, 0.1) : null,
            score: this.createAudioContext() ? this.createSound(400, 0.2) : null,
            gameOver: this.createAudioContext() ? this.createSound(150, 0.5) : null
        };
        
        // Achievements system
        this.achievements = JSON.parse(localStorage.getItem('flappyBirdAchievements') || '{}');
        this.totalGamesPlayed = parseInt(localStorage.getItem('flappyBirdGamesPlayed') || '0');
        
        // Bird properties
        this.bird = {
            x: 80,
            y: 300,
            width: 34,
            height: 24,
            velocity: 0,
            gravity: 0.6,
            jumpPower: -12,
            rotation: 0,
            trail: []
        };
        
        // Pipe properties
        this.pipes = [];
        this.pipeWidth = 52;
        this.pipeGap = 140;
        this.pipeSpeed = 2;
        
        // Power-ups
        this.powerUps = [];
        this.activePowerUps = new Set();
        
        // Particle effects
        this.particles = [];
        
        // Background elements
        this.clouds = [];
        this.groundY = this.canvas.height - 112;
        this.groundX = 0;
        
        // Animation properties
        this.animationTime = 0;
        
        // Initialize
        this.initializeClouds();
        this.setupEventListeners();
        this.updateUI();
        this.gameLoop();
    }
    
    createAudioContext() {
        try {
            return new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            return null;
        }
    }
    
    createSound(frequency, duration) {
        if (!this.audioContext) {
            this.audioContext = this.createAudioContext();
        }
        if (!this.audioContext) return null;
        
        return () => {
            if (!this.soundEnabled) return;
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
            gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
            
            oscillator.start(this.audioContext.currentTime);
            oscillator.stop(this.audioContext.currentTime + duration);
        };
    }
    
    initializeClouds() {
        for (let i = 0; i < 3; i++) {
            this.clouds.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * 200 + 50,
                width: 60 + Math.random() * 40,
                height: 30 + Math.random() * 20,
                speed: 0.2 + Math.random() * 0.3
            });
        }
    }
    
    setupEventListeners() {
        // Start button
        document.getElementById('startBtn').addEventListener('click', () => {
            this.startGame();
        });
        
        // Restart button
        document.getElementById('restartBtn').addEventListener('click', () => {
            this.restartGame();
        });
        
        // Resume button
        document.getElementById('resumeBtn').addEventListener('click', () => {
            this.togglePause();
        });
        
        // Pause button
        document.getElementById('pauseBtn').addEventListener('click', () => {
            this.togglePause();
        });
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                e.preventDefault();
                if (this.gameState === 'playing') {
                    this.flap();
                }
            } else if (e.code === 'Escape') {
                e.preventDefault();
                this.togglePause();
            }
        });
        
        // Mouse/touch controls
        this.canvas.addEventListener('click', () => {
            if (this.gameState === 'playing') {
                this.flap();
            }
        });
    }
    
    startGame() {
        this.gameState = 'playing';
        this.score = 0;
        this.bird.y = 300;
        this.bird.velocity = 0;
        this.pipes = [];
        this.updateUI();
        
        // Play start sound
        if (this.soundEnabled && this.sounds.gameStart) {
            this.sounds.gameStart();
        }
    }
    
    restartGame() {
        this.startGame();
    }
    
    flap() {
        this.bird.velocity = this.bird.jumpPower;
        
        // Add trail effect
        this.bird.trail.push({
            x: this.bird.x + this.bird.width / 2,
            y: this.bird.y + this.bird.height / 2,
            life: 10
        });
        
        // Play flap sound
        if (this.sounds.flap) this.sounds.flap();
        
        // Create particles
        this.createParticles(this.bird.x, this.bird.y, '#FFD700');
    }
    
    checkAchievements() {
        const newAchievements = [];
        
        if (this.score >= 10 && !this.achievements.firstTen) {
            this.achievements.firstTen = true;
            newAchievements.push('First 10 Points!');
        }
        
        if (this.score >= 50 && !this.achievements.fiftyPoints) {
            this.achievements.fiftyPoints = true;
            newAchievements.push('Half Century!');
        }
        
        if (this.totalGamesPlayed >= 10 && !this.achievements.tenGames) {
            this.achievements.tenGames = true;
            newAchievements.push('Persistent Player!');
        }
        
        if (newAchievements.length > 0) {
            localStorage.setItem('flappyBirdAchievements', JSON.stringify(this.achievements));
            this.showAchievement(newAchievements[0]);
        }
    }
    
    showAchievement(text) {
        // Create achievement notification
        const achievement = document.createElement('div');
        achievement.className = 'achievement-popup';
        achievement.textContent = `🏆 ${text}`;
        document.body.appendChild(achievement);
        
        setTimeout(() => {
            if (achievement.parentNode) {
                achievement.parentNode.removeChild(achievement);
            }
        }, 3000);
    }
    
    createPowerUp(x, y) {
        const types = ['shield', 'slowTime', 'doublePoints'];
        const type = types[Math.floor(Math.random() * types.length)];
        
        this.powerUps.push({
            x: x,
            y: y,
            type: type,
            duration: 300, // frames
            collected: false
        });
    }
    
    togglePause() {
        if (this.gameState === 'playing') {
            this.gameState = 'paused';
            this.isPaused = true;
        } else if (this.gameState === 'paused') {
            this.gameState = 'playing';
            this.isPaused = false;
        }
        this.updateUI();
    }
    
    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        localStorage.setItem('flappyBirdSound', this.soundEnabled);
    }
    
    updatePowerUps() {
        if (this.gameState !== 'playing') return;
        
        // Move power-ups
        this.powerUps.forEach((powerUp, index) => {
            powerUp.x -= this.pipeSpeed;
            
            // Check collection
            if (!powerUp.collected && 
                this.bird.x < powerUp.x + 20 && 
                this.bird.x + this.bird.width > powerUp.x &&
                this.bird.y < powerUp.y + 20 && 
                this.bird.y + this.bird.height > powerUp.y) {
                
                powerUp.collected = true;
                this.activePowerUps.add(powerUp.type);
                if (this.sounds.score) this.sounds.score();
                
                // Add particles
                this.createParticles(powerUp.x, powerUp.y, '#FFD700');
            }
            
            // Remove off-screen power-ups
            if (powerUp.x + 20 < 0) {
                this.powerUps.splice(index, 1);
            }
        });
        
        // Randomly spawn power-ups
        if (Math.random() < 0.002 && this.pipes.length > 0) {
            const lastPipe = this.pipes[this.pipes.length - 1];
            this.createPowerUp(lastPipe.x + 100, lastPipe.y + this.pipeGap / 2);
        }
    }
    
    createParticles(x, y, color) {
        for (let i = 0; i < 10; i++) {
            this.particles.push({
                x: x,
                y: y,
                vx: (Math.random() - 0.5) * 8,
                vy: (Math.random() - 0.5) * 8,
                life: 30,
                maxLife: 30,
                color: color
            });
        }
    }
    
    updateParticles() {
        this.particles.forEach((particle, index) => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.vy += 0.2; // gravity
            particle.life--;
            
            if (particle.life <= 0) {
                this.particles.splice(index, 1);
            }
        });
    }
    
    updateDifficulty() {
        // Increase difficulty every 10 points
        const newDifficulty = Math.floor(this.score / 10) + 1;
        if (newDifficulty > this.difficulty) {
            this.difficulty = newDifficulty;
            this.pipeSpeed = Math.min(2 + this.difficulty * 0.5, 5);
            this.pipeGap = Math.max(140 - this.difficulty * 5, 100);
        }
    }
    
    updateBird() {
        if (this.gameState !== 'playing') return;
        
        // Apply gravity
        this.bird.velocity += this.bird.gravity;
        this.bird.y += this.bird.velocity;
        
        // Update rotation based on velocity
        this.bird.rotation = Math.min(Math.max(this.bird.velocity * 3, -30), 90);
        
        // Check ground collision
        if (this.bird.y + this.bird.height > this.groundY) {
            this.gameOver();
        }
        
        // Check ceiling collision
        if (this.bird.y < 0) {
            this.bird.y = 0;
            this.bird.velocity = 0;
        }
    }
    
    updatePipes() {
        if (this.gameState !== 'playing') return;
        
        // Add new pipe
        if (this.pipes.length === 0 || this.pipes[this.pipes.length - 1].x < this.canvas.width - 200) {
            const pipeY = Math.random() * (this.groundY - this.pipeGap - 200) + 100;
            this.pipes.push({
                x: this.canvas.width,
                y: pipeY,
                scored: false
            });
        }
        
        // Move pipes
        this.pipes.forEach((pipe, index) => {
            pipe.x -= this.pipeSpeed;
            
            // Check if pipe is passed and not scored
            if (!pipe.scored && pipe.x + this.pipeWidth < this.bird.x) {
                pipe.scored = true;
                let points = 1;
                
                // Double points power-up
                if (this.activePowerUps.has('doublePoints')) {
                    points = 2;
                }
                
                this.score += points;
                
                // Play score sound
                if (this.soundEnabled && this.sounds.score) {
                    this.sounds.score();
                }
                
                // Create score particles
                this.createParticles(pipe.x + this.pipeWidth/2, pipe.y + this.pipeGap/2, '#00FF00');
                
                this.updateScore();
            }
            
            // Remove pipes that are off screen
            if (pipe.x + this.pipeWidth < 0) {
                this.pipes.splice(index, 1);
            }
            
            // Check collision
            if (this.checkPipeCollision(pipe)) {
                this.gameOver();
            }
        });
    }
    
    checkPipeCollision(pipe) {
        // Check if bird is in pipe's x range
        if (this.bird.x < pipe.x + this.pipeWidth && 
            this.bird.x + this.bird.width > pipe.x) {
            
            // Check if bird hits top or bottom pipe
            if (this.bird.y < pipe.y || 
                this.bird.y + this.bird.height > pipe.y + this.pipeGap) {
                return true;
            }
        }
        return false;
    }
    
    updateClouds() {
        this.clouds.forEach(cloud => {
            cloud.x -= cloud.speed;
            if (cloud.x + cloud.width < 0) {
                cloud.x = this.canvas.width;
                cloud.y = Math.random() * 200 + 50;
            }
        });
    }
    
    updateGround() {
        if (this.gameState === 'playing') {
            this.groundX -= this.pipeSpeed;
            if (this.groundX <= -50) {
                this.groundX = 0;
            }
        }
    }
    
    drawBackground() {
        // Draw sky gradient
        const gradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        gradient.addColorStop(0, '#87CEEB');
        gradient.addColorStop(0.7, '#98D8E8');
        gradient.addColorStop(1, '#90EE90');
        
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw clouds
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        this.clouds.forEach(cloud => {
            this.drawCloud(cloud.x, cloud.y, cloud.width, cloud.height);
        });
    }
    
    drawCloud(x, y, width, height) {
        this.ctx.beginPath();
        this.ctx.arc(x, y, height/2, 0, Math.PI * 2);
        this.ctx.arc(x + width/3, y, height/2.5, 0, Math.PI * 2);
        this.ctx.arc(x + 2*width/3, y, height/2.5, 0, Math.PI * 2);
        this.ctx.arc(x + width, y, height/2, 0, Math.PI * 2);
        this.ctx.fill();
    }
    
    drawGround() {
        // Draw grass
        this.ctx.fillStyle = '#228B22';
        this.ctx.fillRect(0, this.groundY, this.canvas.width, this.canvas.height - this.groundY);
        
        // Draw grass pattern
        this.ctx.fillStyle = '#32CD32';
        for (let x = this.groundX; x < this.canvas.width + 50; x += 50) {
            for (let i = 0; i < 5; i++) {
                const grassX = x + Math.random() * 40;
                const grassHeight = 8 + Math.random() * 12;
                this.ctx.fillRect(grassX, this.groundY, 2, grassHeight);
            }
        }
    }
    
    drawBird() {
        // Draw bird trail
        this.ctx.globalAlpha = 0.3;
        this.bird.trail.forEach((trail, index) => {
            const alpha = trail.life / 10;
            this.ctx.globalAlpha = alpha * 0.3;
            this.ctx.fillStyle = '#FFD700';
            this.ctx.beginPath();
            this.ctx.arc(trail.x, trail.y, 3, 0, Math.PI * 2);
            this.ctx.fill();
            trail.life--;
        });
        this.bird.trail = this.bird.trail.filter(trail => trail.life > 0);
        this.ctx.globalAlpha = 1;
        
        // Apply power-up effects
        if (this.activePowerUps.has('shield')) {
            this.ctx.strokeStyle = '#00FFFF';
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.arc(this.bird.x + this.bird.width/2, this.bird.y + this.bird.height/2, 25, 0, Math.PI * 2);
            this.ctx.stroke();
        }
        
        this.ctx.save();
        this.ctx.translate(this.bird.x + this.bird.width/2, this.bird.y + this.bird.height/2);
        this.ctx.rotate(this.bird.rotation * Math.PI / 180);
        
        // Draw bird body
        this.ctx.fillStyle = '#FFD700';
        this.ctx.fillRect(-this.bird.width/2, -this.bird.height/2, this.bird.width, this.bird.height);
        
        // Draw bird beak
        this.ctx.fillStyle = '#FFA500';
        this.ctx.fillRect(this.bird.width/2 - 2, -3, 8, 6);
        
        // Draw bird eye
        this.ctx.fillStyle = 'white';
        this.ctx.beginPath();
        this.ctx.arc(this.bird.width/4, -this.bird.height/4, 4, 0, Math.PI * 2);
        this.ctx.fill();
        
        this.ctx.fillStyle = 'black';
        this.ctx.beginPath();
        this.ctx.arc(this.bird.width/4 + 1, -this.bird.height/4, 2, 0, Math.PI * 2);
        this.ctx.fill();
        
        this.ctx.restore();
    }
    
    drawPipes() {
        this.ctx.fillStyle = '#228B22';
        this.pipes.forEach(pipe => {
            // Top pipe
            this.ctx.fillRect(pipe.x, 0, this.pipeWidth, pipe.y);
            // Bottom pipe
            this.ctx.fillRect(pipe.x, pipe.y + this.pipeGap, this.pipeWidth, this.canvas.height - pipe.y - this.pipeGap);
            
            // Pipe borders
            this.ctx.strokeStyle = '#006400';
            this.ctx.lineWidth = 3;
            this.ctx.strokeRect(pipe.x, 0, this.pipeWidth, pipe.y);
            this.ctx.strokeRect(pipe.x, pipe.y + this.pipeGap, this.pipeWidth, this.canvas.height - pipe.y - this.pipeGap);
        });
    }
    
    drawPowerUps() {
        this.powerUps.forEach(powerUp => {
            if (powerUp.collected) return;
            
            this.ctx.save();
            this.ctx.translate(powerUp.x + 10, powerUp.y + 10);
            this.ctx.rotate(this.animationTime * 0.05);
            
            // Draw power-up based on type
            switch (powerUp.type) {
                case 'shield':
                    this.ctx.fillStyle = '#00FFFF';
                    this.ctx.fillRect(-8, -8, 16, 16);
                    break;
                case 'slowTime':
                    this.ctx.fillStyle = '#FF69B4';
                    this.ctx.beginPath();
                    this.ctx.arc(0, 0, 8, 0, Math.PI * 2);
                    this.ctx.fill();
                    break;
                case 'doublePoints':
                    this.ctx.fillStyle = '#FFD700';
                    this.ctx.font = '16px Arial';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillText('2X', 0, 5);
                    break;
            }
            
            this.ctx.restore();
        });
    }
    
    drawParticles() {
        this.particles.forEach(particle => {
            const alpha = particle.life / particle.maxLife;
            this.ctx.globalAlpha = alpha;
            this.ctx.fillStyle = particle.color;
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, 2, 0, Math.PI * 2);
            this.ctx.fill();
        });
        this.ctx.globalAlpha = 1;
    }
    
    gameOver() {
        this.gameState = 'gameOver';
        
        // Update best score
        if (this.score > this.bestScore) {
            this.bestScore = this.score;
            localStorage.setItem('flappyBirdBestScore', this.bestScore);
        }
        
        // Update achievements
        this.updateAchievements('score', this.score);
        this.updateAchievements('gamesPlayed', this.totalGamesPlayed);
        
        this.updateUI();
        
        // Play game over sound
        if (this.soundEnabled && this.sounds.gameOver) {
            this.sounds.gameOver();
        }
    }
    
    updateScore() {
        document.getElementById('score').textContent = this.score;
    }
    
    updateUI() {
        const startScreen = document.getElementById('startScreen');
        const gameOverScreen = document.getElementById('gameOverScreen');
        const pauseScreen = document.getElementById('pauseScreen');
        const gameHUD = document.getElementById('gameHUD');
        
        // Hide all screens
        startScreen.classList.add('hidden');
        gameOverScreen.classList.add('hidden');
        pauseScreen.classList.add('hidden');
        gameHUD.classList.add('hidden');
        
        // Show appropriate screen
        switch (this.gameState) {
            case 'start':
                startScreen.classList.remove('hidden');
                break;
            case 'playing':
                gameHUD.classList.remove('hidden');
                this.updateScore();
                this.updateDifficultyDisplay();
                this.updatePowerUpDisplay();
                this.updateSoundButton();
                break;
            case 'paused':
                pauseScreen.classList.remove('hidden');
                gameHUD.classList.remove('hidden');
                break;
            case 'gameOver':
                gameOverScreen.classList.remove('hidden');
                document.getElementById('finalScore').textContent = `Score: ${this.score}`;
                document.getElementById('bestScore').textContent = `Best: ${this.bestScore}`;
                this.checkAchievements();
                break;
        }
    }
    
    updateDifficultyDisplay() {
        const difficultyEl = document.getElementById('difficulty');
        if (difficultyEl) {
            difficultyEl.textContent = `Level: ${this.difficulty}`;
        }
    }
    
    updatePowerUpDisplay() {
        const powerUpEl = document.getElementById('powerUpStatus');
        if (powerUpEl && this.activePowerUps.size > 0) {
            const powerUps = Array.from(this.activePowerUps).join(', ');
            powerUpEl.textContent = `Power-ups: ${powerUps}`;
        } else if (powerUpEl) {
            powerUpEl.textContent = '';
        }
    }
    
    updateSoundButton() {
        const soundBtn = document.getElementById('soundBtn');
        if (soundBtn) {
            soundBtn.textContent = this.soundEnabled ? '🔊' : '🔇';
        }
    }
    
    updateAchievements(type, value) {
        // Update achievements based on type and value
        if (type === 'score') {
            if (value >= 10 && !this.achievements['score10']) {
                this.achievements['score10'] = true;
                alert('Achievement unlocked: Score 10 points!');
            }
            if (value >= 50 && !this.achievements['score50']) {
                this.achievements['score50'] = true;
                alert('Achievement unlocked: Score 50 points!');
            }
            if (value >= 100 && !this.achievements['score100']) {
                this.achievements['score100'] = true;
                alert('Achievement unlocked: Score 100 points!');
            }
        } else if (type === 'gamesPlayed') {
            if (value >= 1 && !this.achievements['play1']) {
                this.achievements['play1'] = true;
                alert('Achievement unlocked: Play 1 game!');
            }
            if (value >= 10 && !this.achievements['play10']) {
                this.achievements['play10'] = true;
                alert('Achievement unlocked: Play 10 games!');
            }
            if (value >= 50 && !this.achievements['play50']) {
                this.achievements['play50'] = true;
                alert('Achievement unlocked: Play 50 games!');
            }
        }
        
        localStorage.setItem('flappyBirdAchievements', JSON.stringify(this.achievements));
    }
    
    showAchievements() {
        const achievementsList = document.getElementById('achievementsList');
        achievementsList.innerHTML = '';
        
        for (const [key, value] of Object.entries(this.achievements)) {
            const listItem = document.createElement('li');
            listItem.textContent = `${key}: ${value ? 'Unlocked' : 'Locked'}`;
            achievementsList.appendChild(listItem);
        }
    }
    
    render() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw everything
        this.drawBackground();
        this.drawGround();
        this.drawPipes();
        this.drawBird();
        this.drawPowerUps();
        this.drawParticles();
    }
    
    update() {
        this.updateBird();
        this.updatePipes();
        this.updateClouds();
        this.updateGround();
        this.updatePowerUps();
        this.updateParticles();
        this.updateDifficulty();
    }
    
    gameLoop() {
        if (this.gameState !== 'paused') {
            this.update();
        }
        this.render();
        this.animationTime++;
        requestAnimationFrame(() => this.gameLoop());
    }
}

// Start the game when the page loads
window.addEventListener('load', () => {
    new FlappyBird();
});
