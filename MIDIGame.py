import pygame
import sys
import random
import math
import numpy as np

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 780, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MIDI Keyboard Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 50)
RED = (255, 50, 50)

# Fonts
font = pygame.font.Font(None, 36)

# Define keys and notes
keys = ["C", "D", "E", "F", "G", "A", "B", "C#", "D#", "F#", "G#", "A#"]
notes = ["do", "re", "mi", "fa", "sol", "la", "si", "do#", "re#", "fa#", "sol#", "la#"]

# Generate sound frequencies for notes
base_frequency = 261.63  # Frequency of middle C
frequencies = [base_frequency * (2 ** (i / 12)) for i in range(len(keys))]
volume = 0.5

# Key dimensions
NUM_KEYS = len(keys)
KEY_WIDTH = WIDTH // NUM_KEYS
KEY_HEIGHT = 100

# Particles
particles = []
active_keys = {} #{key : hold_time}

synthesis_methods = ['Sine Wave', 'Granular Synthesis']
current_method_index = 0
sample_rate = 44100
filter_cutoff = 10000

def apply_filter(wave):
    fft_wave = np.fft.rfft(wave)
    frequencies = np.fft.rfftfreq(len(wave), 1/sample_rate)
    fft_wave[frequencies > filter_cutoff] = 0
    filtered_wave = np.fft.irfft(fft_wave)
    return filtered_wave

def generate_sine_wave(frequency, duration, volume=1.0, mod_depth=0, mod_rate=0):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    if mod_depth > 0 and mod_rate > 0:
        modulation = mod_depth * np.sin(2 * np.pi * mod_rate * t)
        wave = np.sin(2 * np.pi * (frequency + modulation) * t)
    else:
        wave = np.sin(2 * np.pi * frequency * t)
    wave *= volume
    wave = apply_filter(wave)
    wave = np.int16(wave * 32767)
    stereo_wave = np.column_stack((wave, wave))
    stereo_wave = np.ascontiguousarray(stereo_wave)
    return stereo_wave

def generate_granular_wave(frequency, duration, volume=1.0):
    grain_size = 0.02
    t = np.linspace(0, grain_size, int(sample_rate * grain_size), endpoint=False)
    grain = np.sin(2 * np.pi * frequency * t)
    grain *= np.hanning(len(grain))
    num_grains = int(duration / grain_size)
    wave = np.tile(grain, num_grains)
    wave *= volume
    wave = apply_filter(wave)
    wave = np.int16(wave * 32767)
    stereo_wave = np.column_stack((wave, wave))
    stereo_wave = np.ascontiguousarray(stereo_wave)

def generate_tone(frequency, duration=1.0, sample_rate=44100):
    """Generate a tone with a given frequency and duration."""
    duration = 1.0
    if synthesis_methods[current_method_index] == 'Sine Wave':
        wave = generate_sine_wave(frequency, duration, volume, 40, 5)
    elif synthesis_methods[current_method_index] == 'Granular Synthesis':
        wave = generate_granular_wave(frequency, duration, volume)
    # n_samples = int(sample_rate * duration)
    # buffer = (int(32767.0 * math.sin(2.0 * math.pi * frequency * t / sample_rate)) for t in range(n_samples))
    sound = pygame.sndarray.make_sound(pygame.sndarray.array(wave))
    return sound

# Pre-generate sounds for all notes
sounds = [generate_tone(freq) for freq in frequencies]

def draw_keyboard():
    """Draw the keyboard layout."""
    for i, key in enumerate(keys):
        rect = pygame.Rect(i * KEY_WIDTH, HEIGHT - KEY_HEIGHT, KEY_WIDTH, KEY_HEIGHT)
        color = BLUE if i in active_keys else GRAY
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)
        label = font.render(key, True, BLACK if i not in active_keys else WHITE)
        screen.blit(label, (i * KEY_WIDTH + KEY_WIDTH // 4, HEIGHT - KEY_HEIGHT // 2))

def handle_key_press(index):
    """Handle key press events: visual and audio feedback."""
    if index not in active_keys:
        active_keys[index] = 1

        # Play sound
        sounds[index].play(-1)
        

def handle_key_release(index):
    """Handle key release events."""
    if index in active_keys:
        active_keys.pop(index, None)
        sounds[index].stop()

def draw_particles():
    """Draw particle effects."""
    for particle in particles[:]:
        particle[0] += particle[2]  # Move horizontally
        particle[1] += particle[3]  # Move vertically
        pygame.draw.circle(screen, particle[4], (int(particle[0]), int(particle[1])), 5)
        if particle[1] < 0 or particle[0] < 0 or particle[0] > WIDTH:
            particles.remove(particle)

key_map = {
                pygame.K_a: 0, pygame.K_s: 1, pygame.K_d: 2, pygame.K_f: 3,
                pygame.K_g: 4, pygame.K_h: 5, pygame.K_j: 6, pygame.K_w: 7,
                pygame.K_e: 8, pygame.K_t: 9, pygame.K_y: 10, pygame.K_u: 11
            }

def loop_events():
    actived_keys = ""
    for index in active_keys.keys():
        # Add particles
        actived_keys += notes[index] + " + "
        active_keys[index] += 0.001
        time = min(int(active_keys[index]), 100)
        for _ in range(time):
            particles.append([
                random.randint(index * KEY_WIDTH, (index + 1) * KEY_WIDTH),
                HEIGHT - KEY_HEIGHT,
                random.uniform(-2, 2),
                random.uniform(-5, -1),
                random.choice([BLUE, YELLOW, RED])
            ])
            
    #Music note Bar
    pygame.draw.rect(screen, WHITE, pygame.Rect(0, 0, WIDTH, 40))
    # Display music note on canvas
    note_label = font.render(actived_keys[:-3], True, BLACK)
    screen.blit(note_label, (10, 8))


# Game loop
running = True
while running:
    screen.fill(BLACK)
    
    loop_events()
    
    draw_keyboard()
    draw_particles()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key in key_map:
                handle_key_press(key_map[event.key])
                
        if event.type == pygame.KEYUP:
            if event.key in key_map:
                handle_key_release(key_map[event.key])

    pygame.display.flip()

pygame.quit()
sys.exit()
