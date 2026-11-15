"""Stable interface shared by vision and AudioLDM 2 teams.
Audio parameters below describe desired sound qualities, NOT sound facts in an image.
"""
from pydantic import BaseModel, Field
from typing import Literal

Scene = Literal['forest', 'coast', 'desert', 'river', 'waterfall', 'mountain', 'lake', 'unknown']
Intensity = Literal['gentle', 'moderate', 'strong']

class SoundSettings(BaseModel):
    scene: Scene = 'forest'
    sound: Literal['rain', 'sea_waves', 'wind', 'pouring_water', 'thunderstorm'] = 'rain'
    intensity: Intensity = 'gentle'
    comfort_mode: bool = True
    seconds: int = Field(default=10, ge=5, le=30)

SCENES = {
    'forest': 'a peaceful forest with tall trees',
    'coast': 'a quiet natural coastline',
    'desert': 'a wide tranquil desert landscape',
    'river': 'a scenic river valley',
    'waterfall': 'a rocky waterfall surrounded by nature',
    'mountain': 'a remote mountain landscape',
    'lake': 'a calm lakeside landscape',
    'unknown': 'a peaceful outdoor natural environment',
}
SOUNDS = {
    'rain': 'rain falling steadily',
    'sea_waves': 'gentle ocean waves rolling onto the shore',
    'wind': 'wind softly moving through the surroundings',
    'pouring_water': 'flowing and trickling freshwater',
    'thunderstorm': 'a distant rumbling thunderstorm',
}

def build_prompt(settings: SoundSettings) -> dict:
    environment = SCENES[settings.scene]
    event = SOUNDS[settings.sound]
    strength = {
        'gentle': 'very soft, delicate and unobtrusive',
        'moderate': 'natural and moderately present',
        'strong': 'full and clearly audible',
    }[settings.intensity]
    style = 'Smooth relaxing ambience, no sudden loud events.' if settings.comfort_mode else 'Natural dynamic environmental ambience.'
    prompt = f'The natural sound of {event} in {environment}. {strength.capitalize()} acoustic texture. {style} High-fidelity field recording quality, no music, no speech.'
    return {
        'prompt': prompt,
        'negative_prompt': 'speech, voices, music, engines, traffic, distortion, harsh clicks, digital artifacts',
        'settings': settings.model_dump(),
        'note': 'This is a requested audio description; scene detection does not prove the sound exists in the photo.',
    }
