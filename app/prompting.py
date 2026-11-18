"""Stable interface shared by vision and AudioLDM 2 teams.
Audio parameters below describe desired sound qualities, NOT sound facts in an image.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Literal

Scene = Literal['forest', 'coast', 'desert', 'river', 'waterfall', 'mountain', 'lake', 'unknown']
Intensity = Literal['gentle', 'moderate', 'strong']
Sound = Literal['rain', 'sea_waves', 'wind', 'pouring_water', 'thunderstorm']

class SoundSettings(BaseModel):
    scene: Scene = 'forest'
    sound: Sound = 'rain'
    levels: dict[Sound, int] | None = None
    preset: Literal['relax', 'sleep', 'focus', 'nature'] = 'relax'
    intensity: Intensity = 'gentle'
    comfort_mode: bool = True
    weather: Literal['none', 'rain', 'snow', 'fog', 'wind'] = 'none'
    seconds: int = Field(default=10, ge=5, le=30)

    @field_validator('levels')
    @classmethod
    def validate_levels(cls, value):
        if value is not None and (not value or not any(value.values()) or any(v < 0 or v > 100 for v in value.values())):
            raise ValueError('Choose at least one sound level between 0 and 100')
        return value

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
    'sea_waves': 'gentle ocean waves',
    'wind': 'soft wind',
    'pouring_water': 'flowing water',
    'thunderstorm': 'distant thunder',
}

def build_prompt(settings: SoundSettings) -> dict:
    environment = SCENES[settings.scene]
    active = sorted(((name, level) for name, level in (settings.levels or {settings.sound: 100}).items() if level), key=lambda item: -item[1])
    event = ', '.join(SOUNDS[name] for name, _ in active)
    strength = {
        'gentle': 'very soft, delicate and unobtrusive',
        'moderate': 'natural and moderately present',
        'strong': 'full and clearly audible',
    }[settings.intensity]
    style = 'Smooth relaxing ambience, no sudden loud events.' if settings.comfort_mode else 'Natural dynamic environmental ambience.'
    weather = '' if settings.weather == 'none' else f' The listener imagines {settings.weather} in the scene.'
    mood = {'relax': 'a restful atmosphere', 'sleep': 'a quiet sleep-time atmosphere',
            'focus': 'an unobtrusive atmosphere for focus', 'nature': 'a natural outdoor atmosphere'}[settings.preset]
    prompt = f'The natural sounds of {event} in {environment}.{weather} {strength.capitalize()} texture, {mood}. {style} No music or speech.'
    return {
        'prompt': prompt,
        'negative_prompt': 'speech, voices, music, engines, traffic, distortion, harsh clicks, digital artifacts',
        'settings': settings.model_dump(),
        'note': 'This is a requested audio description; scene detection does not prove the sound exists in the photo.',
    }
