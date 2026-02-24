#!/usr/bin/env python3
"""Generate story illustrations using Google Imagen via Vertex AI.

Uses the same gcloud ADC auth as the TTS/translation scripts.
Style matches existing illustrations: traditional Indian watercolor storybook art.
"""

import argparse
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

PROJECT_ID = "tts-stories-488001"
LOCATION = "us-central1"

STYLE_PREFIX = (
    "Traditional Indian watercolor storybook illustration for children. "
    "Warm earthy and golden tones, soft brushstrokes, detailed traditional Indian setting. "
    "Style of classic Indian children's book art with Mughal miniature painting influences. "
    "No text or letters in the image. "
)


def generate_image(prompt: str, output_path: str, aspect_ratio: str = "3:4"):
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")

    full_prompt = STYLE_PREFIX + prompt
    print(f"Generating image with prompt:\n{full_prompt}\n")

    response = model.generate_images(
        prompt=full_prompt,
        number_of_images=1,
        aspect_ratio=aspect_ratio,
    )

    if response.images:
        response.images[0].save(location=output_path)
        print(f"Saved to {output_path}")
    else:
        print("No image generated.")


def main():
    parser = argparse.ArgumentParser(description="Generate a story illustration")
    parser.add_argument("--prompt", required=True, help="Scene description for the illustration")
    parser.add_argument("--output", required=True, help="Output file path (PNG)")
    parser.add_argument("--aspect", default="3:4", help="Aspect ratio (default: 3:4)")
    args = parser.parse_args()

    generate_image(args.prompt, args.output, args.aspect)


if __name__ == "__main__":
    main()
