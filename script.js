class FlappyBird {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Game state
        this.gameState = 'start'; // 'start', 'playing', 'gameOver'
        this.score = 0;
        this.bestScore = localStorage.getItem('flappyBirdBestScore') || 0;
        
        // Bird properties
        this.bird = {
            x: 80,
            y: 300,
            width: 34,
            height: 24,
            velocity: 0,
            gravity: 0.6,
            jumpPower: -12,
            rotation: 0
        };
        
        // Pipe properties
        this.pipes = [];
        this.pipeWidth = 52;
        this.pipeGap = 140;
        this.pipeSpeed = 2;
        
        // Background elements
        this.clouds = [];
        this.groundY = this.canvas.height - 112;
        this.groundX = 0;
        
        // Initialize
        this.initializeClouds();
        this.setupEventListeners();
        this.updateUI();
        this.gameLoop();
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
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                e.preventDefault();
                if (this.gameState === 'playing') {
                    this.flap();
                }
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
    }
    
    restartGame() {
        this.startGame();
    }
    
    flap() {
        this.bird.velocity = this.bird.jumpPower;
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
                this.score++;
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
    
    gameOver() {
        this.gameState = 'gameOver';
        
        // Update best score
        if (this.score > this.bestScore) {
            this.bestScore = this.score;
            localStorage.setItem('flappyBirdBestScore', this.bestScore);
        }
        
        this.updateUI();
    }
    
    updateScore() {
        document.getElementById('score').textContent = this.score;
    }
    
    updateUI() {
        const startScreen = document.getElementById('startScreen');
        const gameOverScreen = document.getElementById('gameOverScreen');
        const gameHUD = document.getElementById('gameHUD');
        
        // Hide all screens
        startScreen.classList.add('hidden');
        gameOverScreen.classList.add('hidden');
        gameHUD.classList.add('hidden');
        
        // Show appropriate screen
        switch (this.gameState) {
            case 'start':
                startScreen.classList.remove('hidden');
                break;
            case 'playing':
                gameHUD.classList.remove('hidden');
                this.updateScore();
                break;
            case 'gameOver':
                gameOverScreen.classList.remove('hidden');
                document.getElementById('finalScore').textContent = `Score: ${this.score}`;
                document.getElementById('bestScore').textContent = `Best: ${this.bestScore}`;
                break;
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
    }
    
    update() {
        this.updateBird();
        this.updatePipes();
        this.updateClouds();
        this.updateGround();
    }
    
    gameLoop() {
        this.update();
        this.render();
        requestAnimationFrame(() => this.gameLoop());
    }
}

// Start the game when the page loads
window.addEventListener('load', () => {
    new FlappyBird();
});
