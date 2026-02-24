#!/usr/bin/env python3
"""Generate illustrations for all stories missing images using Google Imagen 3.

Reads each story JSON, crafts a scene-specific prompt per section,
generates the image, saves it, and updates the story JSON with image references.
Also updates the Hindi translation JSON if it exists.

Uses gcloud ADC auth (same as TTS/translation scripts).
"""

import json
import os
import sys
import time
import argparse
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

PROJECT_ID = "tts-stories-488001"
LOCATION = "us-central1"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN_DIR = os.path.join(REPO_ROOT, "stories", "en")
HI_DIR = os.path.join(REPO_ROOT, "stories", "hi")
IMAGES_DIR = os.path.join(REPO_ROOT, "stories", "images")

STYLE_PREFIX = (
    "Traditional Indian watercolor storybook illustration for children. "
    "Warm earthy and golden tones, soft brushstrokes, detailed traditional Indian setting. "
    "Style of classic Indian children's book art with Mughal miniature painting influences. "
    "No text, letters, or words in the image. "
)

# Scene prompts per story — each list entry is a prompt for that section index.
# These are hand-crafted to match the story content and produce cohesive illustrations.
STORY_PROMPTS = {
    "epic-arjuna-fish-eye": [
        "Ancient Indian royal court scene. A grand competition arena with princes and warriors gathered. King Drupada sits on a golden throne. A wooden fish target hangs from a high pole. Decorative pillars and banners.",
        "Young princes attempting archery, failing to hit the target. Frustrated warriors with bows. The wooden fish spinning on the pole above. Crowd watching from pavilions.",
        "Arjuna, a handsome young warrior prince, steps forward confidently with his bow. He looks only at the reflection of the fish in a pool of oil below. Other warriors watch in amazement.",
        "Close-up of Arjuna drawing his bow with intense focus. His eyes fixed downward at the water reflection. The spinning wooden fish target visible above. Golden light around him.",
        "Arjuna's arrow piercing the eye of the wooden fish target. The fish falling. The crowd erupting in celebration. Flower petals in the air.",
        "Princess Draupadi placing a flower garland around Arjuna's neck in a victory ceremony. Royal court celebrating. Festive Indian atmosphere with oil lamps and flowers.",
    ],
    "epic-bridge-to-lanka": [
        "Lord Rama standing on the southern shore of India, gazing across a vast ocean toward Lanka. Monkey army of Vanara warriors gathered behind him. Dramatic sunset sky over the sea.",
        "Nala the architect Vanara directing monkeys and bears to carry massive boulders and rocks. Monkeys writing 'Rama' on stones. Ocean waves crashing on rocks.",
        "A small squirrel rolling in wet sand and then rolling on the bridge stones to fill gaps. Lord Rama gently stroking the squirrel's back with three fingers, leaving stripe marks.",
        "Massive stone bridge being built across the ocean. Thousands of monkeys working together carrying rocks. The bridge stretching toward a distant island. Dramatic ocean scene.",
        "The completed Ram Setu bridge stretching across the blue ocean. Rama's entire army marching across triumphantly toward Lanka. Mountains visible on the distant island.",
    ],
    "epic-draupadi-akshaya-patra": [
        "The Pandavas in exile in a dense Indian forest. Simple leaf huts in a forest clearing. Draupadi cooking in a simple outdoor kitchen. Tired but dignified royal family in simple clothes.",
        "Sage Durvasa arriving with hundreds of disciples at the forest ashram. The fierce sage with matted hair. Pandavas looking worried but respectful.",
        "Draupadi alone, anxiously looking at an empty cooking vessel (Akshaya Patra). She is praying with folded hands. Simple forest setting with a cooking fire.",
        "Lord Krishna appearing before Draupadi with divine light around him. He is smiling warmly. Draupadi showing him the empty vessel with tears. Forest hut setting.",
        "Krishna finding one grain of rice and a tiny leaf stuck to the Akshaya Patra vessel. He eats it with a satisfied smile. Divine golden glow emanating.",
        "Sage Durvasa and all his disciples suddenly feeling full, holding their stomachs. They are turning away from the forest ashram. Pandavas relieved and grateful in the background.",
    ],
    "epic-hanuman-mountain": [
        "Epic battle scene in Lanka. Rama's monkey army fighting demon warriors. Arrows and maces in the air. Dramatic twilight sky with fire and smoke.",
        "Lakshmana lying wounded on the battlefield, an arrow in his chest. Rama kneeling beside him, grief-stricken. Monkey warriors gathered around looking sorrowful.",
        "Jambavan the wise old bear telling Hanuman about the Sanjeevani herb. He points northward. Hanuman listening intently. Moonlit battlefield scene.",
        "Hanuman flying through the night sky, growing enormous in size. He soars over oceans and mountains. Stars and moonlight. His mace in hand, orange dhoti flowing.",
        "Giant Hanuman lifting an entire mountain (Dronagiri) on his palm. The mountain has glowing herbs and plants. He flies through a dawn sky carrying the mountain.",
        "Hanuman arriving back with the mountain. The healing herb's fragrance reviving Lakshmana. Rama embracing Hanuman with tears of joy. Golden morning light on the battlefield.",
    ],
    "epic-krishna-butter-mischief": [
        "Baby Krishna as a toddler in the village of Vrindavan. Blue-skinned baby with big dark eyes, curly black hair, peacock feather, golden jewelry. Crawling playfully near clay pots. Mother Yashoda in the background. Rustic village courtyard.",
        "Naughty baby Krishna standing on the shoulders of his cowherd friends, reaching up to a butter pot hanging from the ceiling by ropes. Butter smeared on his face. Simple Indian kitchen with clay pots.",
        "Baby Krishna and his little cowherd friends sneaking into a neighbor's house to steal butter. Village ladies (gopis) looking surprised and amused. Colorful saris, clay butter pots.",
        "Mother Yashoda peeking through a doorway, catching baby Krishna standing on a wooden mortar, hands in the butter pot. Butter all over his face and hands. His mischievous expression. Warm kitchen light.",
        "Mother Yashoda trying to tie baby Krishna to a large wooden mortar with a rope, but the rope keeps being too short. Krishna looking innocent with butter on his cheeks. Courtyard scene.",
    ],
    "epic-ram-golden-deer": [
        "A beautiful enchanted golden deer (Maricha in disguise) with glittering jeweled spots in a lush forest. The deer glows with magical golden light. Dense Indian forest with tropical trees.",
        "Sita pointing excitedly at the golden deer from a forest hut. Rama holding his bow, looking cautious. Lakshmana standing guard. Beautiful forest ashram setting.",
        "Rama chasing the golden deer through the forest with his bow drawn. The deer leaping gracefully ahead. Dappled forest sunlight through canopy.",
        "The golden deer transforming into the demon Maricha as Rama's arrow strikes it. Magical smoke and sparks. The demon's true form emerging. Dark forest atmosphere.",
        "Lakshmana reluctantly leaving Sita alone, drawing a protective glowing line (Lakshman Rekha) around the hut with his arrow. Sita standing at the doorway looking worried. Forest hut.",
        "The demon king Ravana disguised as a sage standing outside the Lakshman Rekha line. Sita offering him food from inside the boundary. Ominous shadows behind the sage. Forest setting.",
    ],
    "panchatantra-thirsty-crow": [
        "A tired, thirsty crow flying over a dry, sun-scorched Indian landscape. Cracked earth, wilted plants, no water anywhere. Hot summer sun blazing. Parched trees.",
        "The crow spotting a tall clay water pitcher (matka) near a tree. The crow landing eagerly beside it. Dry dusty ground. The pitcher is half-buried.",
        "The crow peering into the narrow mouth of the clay pitcher, seeing water far below at the bottom. The crow's beak cannot reach. Frustration on its face.",
        "The crow looking around thoughtfully, spotting small pebbles scattered on the ground near the pitcher. A moment of clever realization. Bright eye.",
        "The crow picking up pebbles one by one in its beak and dropping them into the clay pitcher. Water level slowly rising. Several pebbles visible in the water.",
        "The water risen to the top of the pitcher. The happy crow drinking cool water from the rim. Refreshed and satisfied. Sunset glow. Pebbles visible through the water.",
    ],
    "puranic-dhruv-tara": [
        "Little prince Dhruva, a small boy of five, being pushed away from his father King Uttanapada's lap by his stepmother Suruchi. The king looking helpless on his throne. Royal Indian palace court.",
        "Young Dhruva walking alone into a deep forest, determined. Dense Indian forest with tall ancient trees. The small boy looks resolute despite tears. Twilight forest light.",
        "Sage Narada appearing before young Dhruva in the forest. The divine sage glowing with light, holding his veena. Dhruva looking up with hope. Magical forest clearing.",
        "Young Dhruva sitting in deep meditation (tapasya) on one leg, eyes closed. Forest animals gathered peacefully around him — deer, birds, rabbits. Divine light streaming down. Seasons changing around him.",
        "Lord Vishnu appearing before Dhruva in magnificent divine form. Four-armed Vishnu with conch, discus, mace, and lotus. Brilliant golden-blue divine light. Dhruva bowing in devotion.",
        "Dhruva being reunited with his father the king. The king embracing the boy with tears. The stepmother looking ashamed. Royal palace celebration.",
        "The night sky with one bright star — Dhruva Tara (the Pole Star) — shining above all others. Dhruva's face visible in the star's glow. Indian village below looking up at the eternal star.",
    ],
    "puranic-durga-mahishasura": [
        "The mighty buffalo demon Mahishasura with a crown, terrorizing the heavens. Devas (gods) fleeing in fear. Dark thunderous sky. The demon laughing on a throne of skulls.",
        "All the gods — Brahma, Vishnu, Shiva — channeling their divine energy. Brilliant beams of light from each god converging into one blazing point. Cosmic divine setting.",
        "Goddess Durga taking form from the combined divine light. She is magnificent with multiple arms, radiant golden skin, fierce yet beautiful face. Red sari, crown, divine weapons forming in each hand.",
        "Goddess Durga riding her lion mount into battle. She carries a trident, sword, bow, discus, and other divine weapons in her many arms. Her red sari flowing. Dramatic sky with lightning.",
        "Epic battle between Durga on her lion and Mahishasura who shapeshifts between buffalo, lion, and elephant forms. Weapons clashing. Dramatic action. Fire and divine light.",
        "Durga's trident piercing Mahishasura as he emerges from the buffalo form. The demon defeated. Divine light flooding the scene. The gods showering flowers from heaven.",
        "Victorious Goddess Durga standing tall on the defeated buffalo demon. Serene powerful expression. Devas and celestial beings celebrating. Flowers raining from the sky. Golden divine light.",
    ],
    "puranic-ganesha-head": [
        "Goddess Parvati in her chambers on Mount Kailash, creating a boy from sandalwood paste and turmeric. She lovingly shapes the figure of a child. Divine Himalayan palace setting.",
        "Young Ganesha, a handsome boy, standing guard at the entrance of Parvati's bathing chambers. He holds a staff. Determined, loyal expression. Mountain palace entrance.",
        "Lord Shiva arriving at the palace entrance, being stopped by young Ganesha. Shiva looking surprised and then angry. The boy refuses to let him pass. Tension in the scene.",
        "A dramatic battle between Shiva and young Ganesha. Shiva's trident glowing. The boy fighting bravely. Ganesha's staff broken. Divine energy swirling. Mountain landscape.",
        "Parvati devastated and angry upon finding what happened. Shiva realizes his mistake. He sends his Ganas to find a new head. An elephant sleeping with its head northward under a banyan tree in a peaceful forest.",
        "Lord Ganesha reborn with an elephant head, blessed by all the gods. Shiva and Parvati lovingly looking at their son. The elephant-headed boy glowing with divine light. Flowers and divine blessings showering. Mount Kailash celebration.",
    ],
    "puranic-hanuman-sun": [
        "Baby Hanuman as a tiny monkey child in a forest home. His mother Anjana, a beautiful vanara woman, holding baby Hanuman. Simple forest dwelling. Dawn light.",
        "Baby Hanuman leaping high into the sky toward the rising sun, thinking it is a ripe orange fruit. The tiny monkey flying higher and higher. Clouds around him. The sun glowing ahead.",
        "Baby Hanuman reaching toward the blazing sun with outstretched hands. Rahu the shadow demon also approaching the sun from another direction, looking alarmed at the monkey baby.",
        "Indra the king of gods on his white elephant Airavata, throwing his thunderbolt (vajra) at baby Hanuman in the sky. The bolt striking Hanuman's jaw. Dramatic sky scene.",
        "Baby Hanuman falling from the sky, injured on his chin/jaw. Vayu the wind god catching his son, angry and grief-stricken. He withdraws all wind from the world. Stillness in nature.",
        "All the gods blessing baby Hanuman with divine powers. Brahma, Vishnu, Shiva, Indra, Surya each giving a boon. The baby monkey glowing with accumulated divine blessings. Celestial setting.",
    ],
    "puranic-krishna-govardhan": [
        "Village of Vrindavan preparing for Indra Puja. Villagers decorating with flowers and making offerings. Young Krishna (blue-skinned boy with peacock feather) observing. Festive rural Indian atmosphere.",
        "Young Krishna convincing the villagers to worship Govardhan mountain instead of Indra. He points to the lush green mountain. Villagers listening intently. Cows grazing on the mountain slopes.",
        "Dark storm clouds gathering. Angry Indra on his elephant in the sky commanding terrible rain and thunder. The village being lashed by torrential rain and fierce winds.",
        "Young Krishna effortlessly lifting the massive Govardhan mountain on his little finger. Villagers and cows taking shelter underneath. Rain pouring all around but the people are dry and safe. Dramatic composition.",
        "Seven days passing — Krishna still holding the mountain. Villagers living peacefully underneath, cooking and playing. Cows resting. Krishna smiling. Continuous rain outside.",
        "Indra descending from the clouds, humbled. He bows before Krishna with folded hands. The rain stopping. Rainbow in the sky. Villagers celebrating. Krishna gently setting down the mountain.",
    ],
    "puranic-moon-marks": [
        "Young Lord Ganesha riding a mouse through a moonlit Indian forest. He has a big round belly full of modaks (sweets). A plate of modaks beside him. Peaceful night scene.",
        "A snake suddenly appearing on the forest path. Ganesha's mouse startled and tripping. Ganesha tumbling off, his belly bursting open, modaks spilling everywhere. Comic scene.",
        "Ganesha gathering the modaks back, picking up the snake and tying it as a belt around his belly to hold it together. Clever, slightly embarrassed expression. Moonlit forest.",
        "The full moon in the sky laughing at Ganesha. The moon has a face, laughing mockingly. Ganesha looking up, embarrassed and then angry. Night sky scene.",
        "Angry Ganesha breaking off one of his tusks and hurling it at the laughing moon. The tusk flying through the night sky toward the moon. Dramatic celestial scene.",
        "The moon now has dark marks/spots where the tusk hit. The moon looking chastened and apologetic. Ganesha sitting content with his single tusk. Peaceful night with the now-marked moon.",
    ],
    "puranic-prahlad-holika": [
        "Young prince Prahlad, a gentle devout boy, praying to Lord Vishnu in a dark demon palace. His father, the fearsome demon king Hiranyakashipu, towers behind him angrily. Dark opulent demon throne room.",
        "Hiranyakashipu trying to harm young Prahlad — soldiers with weapons, snakes, fire — but each time a divine protective glow shields the boy. Prahlad remains peaceful in prayer.",
        "Hiranyakashipu ordering elephants to trample Prahlad. The elephants stopping before the praying boy, gently touching him with their trunks instead. The demon king furious. Palace courtyard.",
        "Prahlad's aunt Holika, a demoness with a fire-proof shawl, sitting in a bonfire with young Prahlad on her lap. The fireproof shawl flying off Holika and wrapping around Prahlad. Fire blazing.",
        "Holika burning in the fire while Prahlad sits unharmed, protected by the divine shawl and Vishnu's grace. Prahlad calmly chanting. The bonfire scene. Villagers watching in awe.",
        "Lord Vishnu appearing as Narasimha (half-man, half-lion) from a palace pillar. The fierce divine form with a lion's mane. Hiranyakashipu looking terrified. Dramatic twilight scene at the palace doorway threshold.",
    ],
    "puranic-samudra-manthan": [
        "Devas (gods) and Asuras (demons) facing each other across the cosmic Milky Ocean. The vast ocean stretching to the horizon. Dramatic celestial sky. Both armies assembled.",
        "Mount Mandara being placed in the center of the ocean as a churning rod. The great serpent Vasuki being wrapped around the mountain. Lord Vishnu as the giant turtle Kurma supporting the mountain from below.",
        "Devas pulling one end of Vasuki and Asuras pulling the other. The mountain spinning. The ocean churning with massive waves. Cosmic scale churning scene.",
        "Terrible poison (Halahala) rising from the churning ocean as dark purple-black smoke. Everyone fleeing in terror. The ocean turning dark.",
        "Lord Shiva drinking the poison. Goddess Parvati pressing his throat so the poison stays there, turning his throat blue (Neelkanth). Divine sacrificial moment.",
        "Treasures emerging from the ocean — Goddess Lakshmi on a lotus, the divine white horse Ucchaishravas, the wish-fulfilling cow Kamadhenu, the crescent moon. Golden divine light from the ocean.",
        "Lord Dhanvantari emerging from the ocean holding the pot of Amrita (nectar of immortality). Golden glowing nectar. Devas and Asuras reaching for it. Climactic celestial scene.",
    ],
    "saint-kabir": [
        "Medieval Indian city of Varanasi (Kashi). The ghats along the Ganges river. A humble weaver's home near the river. A baby found in a basket near the water. Dawn over the Ganges.",
        "Young Kabir as a weaver sitting at his handloom, weaving cloth. Simple mud house. He looks contemplative. Threads of different colors on the loom. Varanasi rooftops visible through the window.",
        "Kabir singing devotional poetry in a gathering of both Hindu and Muslim followers. Simple open courtyard. People of different faiths sitting together. Oil lamps. Evening atmosphere.",
        "Kabir meeting the guru Ramananda on the ghats of Varanasi at dawn. The old sage stepping on young Kabir who lies on the steps. The word 'Ram' being uttered. Ganges river, misty morning.",
        "Kabir being challenged by religious authorities — both Hindu priests and Muslim clerics arguing with him. Kabir standing calmly with a gentle smile. Medieval Indian court or marketplace setting.",
        "Kabir weaving at his loom in old age, at peace. His poems floating in the air as golden light. Followers of both faiths sitting around him. Simple home. Spiritual atmosphere. Varanasi skyline.",
    ],
    "saint-mirabai": [
        "Young princess Mirabai as a child in a Rajput palace in Rajasthan. She receives a small idol of Lord Krishna from a wandering saint. The little girl clutching the idol lovingly. Ornate Rajasthani palace.",
        "Mirabai singing and dancing ecstatically before a Krishna idol in a temple. She wears a simple white sari despite being a princess. Devotees watching. Temple bells. Oil lamps. Rajasthani architecture.",
        "Mirabai's royal in-laws trying to stop her devotion. They look disapproving and angry in a grand Rajput palace. Mirabai continuing to sing unfazed, eyes closed in devotion. Courtyard confrontation.",
        "Mirabai drinking from a cup of poison sent by her in-laws, but remaining unharmed. The poison transforming into nectar. Divine glow around her. Krishna's protective presence visible as a shadow. Palace chamber.",
        "Mirabai walking away from the palace, leaving behind royal life. She carries only her ektara (one-string instrument) and Krishna idol. Desert Rajasthan landscape. Freedom and devotion. Sunrise on the road to Vrindavan.",
    ],
    "saint-shankaracharya-chandala": [
        "Young Adi Shankaracharya as a brilliant young sanyasi (monk) walking through the streets of Varanasi with his disciples. Saffron robes, rudraksha beads. Ancient Varanasi street with temples and ghats.",
        "A chandala (outcaste man) with four dogs approaching from the opposite direction on a narrow lane. Shankaracharya's disciples gesturing for the man to move aside. Tension in the narrow street.",
        "Shankaracharya himself about to ask the chandala to step aside. The chandala standing firm, dignified but humble, looking directly at Shankaracharya. Ancient Varanasi narrow lane.",
        "The chandala speaking profound words — 'Which self should step aside? The body or the Atman?' — divine light emanating from him. Shankaracharya looking struck with realization. The dogs peaceful.",
        "Shankaracharya bowing deeply before the chandala with folded hands. His disciples shocked and confused. The chandala glowing with divine wisdom. The narrow lane of Varanasi.",
        "Shankaracharya teaching his disciples the lesson, gesturing to all people around — Brahmins, merchants, workers. The realization that all souls are one. Temple steps of Varanasi. Ganges in the background.",
    ],
    "saint-tulsidas": [
        "Medieval Varanasi. Young Tulsidas as a love-struck husband crossing the Yamuna river at night in a terrible storm, clinging to what he thinks is a log but is actually a floating corpse. Dark stormy night. River waves.",
        "Tulsidas climbing to his wife Ratnavali's window using what he thinks is a rope but is actually a snake. His wife inside looking shocked. Dark night, lightning illuminating the scene. Medieval Indian house.",
        "Ratnavali scolding Tulsidas: pointing from the snake and corpse to a Krishna idol. Tulsidas having a moment of awakening and shame. Simple medieval room with an oil lamp.",
        "Tulsidas renouncing worldly life, sitting at the ghats of Varanasi with a writing stylus and palm leaves. He begins writing. The Ganges flowing behind him. Saffron robes. Serene determination.",
        "Tulsidas writing the Ramcharitmanas (Ramayana in Hindi). Stacks of manuscripts around him. Divine inspiration shown as Lord Rama and Hanuman appearing faintly in golden light above him as he writes.",
        "Old Tulsidas at Tulsi Ghat in Varanasi, surrounded by common people listening to his Ramayana recitation. Everyone — rich and poor — sitting together, moved to tears. Evening lamps along the ghat. Ganges river.",
    ],
    "saint-vivekananda-chicago": [
        "Young Narendranath (future Vivekananda) sitting at the feet of Sri Ramakrishna at the Dakshineswar Kali temple near Kolkata. The master in simple white, the young man in Bengali dhoti. Temple garden setting.",
        "Swami Vivekananda as a wandering monk traveling across India. He walks through diverse landscapes — villages, mountains, temples, and poverty-stricken areas. Saffron robes, turban. Compassion in his eyes.",
        "Vivekananda standing at the tip of a rock in the ocean at Kanyakumari (Cape Comorin), meditating. The southernmost tip of India. Three oceans meeting. Sunrise. Dramatic rock-and-ocean scene.",
        "The grand World Parliament of Religions hall in Chicago, 1893. A vast ornate Western hall filled with delegates from many religions. Vivekananda in saffron turban and robes about to stand. International audience.",
        "Vivekananda at the podium, arms slightly raised, speaking passionately. 'Sisters and Brothers of America.' The enormous audience giving a standing ovation. American flags and religious banners. Powerful oratory moment.",
        "Vivekananda surrounded by admirers in both Indian and Western settings. His legacy shown symbolically — the Ramakrishna Mission, books, young monks, and the awakening of India's spiritual confidence. Montage style.",
    ],
    "vedic-agni-hymn": [
        "Ancient Vedic rishis sitting around a sacred fire altar (havan kund) in a forest hermitage. The fire blazing bright with golden flames. Dawn sky. Chanting atmosphere. Simple thatched-roof ashram.",
        "The fire god Agni — a radiant figure with golden-red skin and flames for hair — emerging from the sacred fire. Two faces, seven tongues of flame, a ram nearby. Vedic cosmic setting.",
        "Vedic fire ceremony (yajna) in progress. Priests pouring ghee (clarified butter) into the fire. The fire leaping higher with each offering. Sacred chanting symbols in the air. Dawn light.",
        "Agni as the messenger carrying offerings upward to the gods in the sky. Trails of golden fire rising from the altar to the heavens. Devas receiving the offerings above the clouds.",
        "A Vedic household — a family lighting their cooking fire, the father performing a small home fire ritual. Agni present in the humble domestic hearth. Warm, intimate household scene.",
        "The eternal flame — a sacred fire that has been kept burning for generations, tended by Vedic priests. Ancient and timeless atmosphere. Forest hermitage. Stars above. The fire connects earth to sky.",
    ],
    "wisdom-king-and-ring": [
        "A wise old Indian king on his throne, looking troubled despite his wealth. Grand but heavy-hearted. He summons his wisest ministers. Ornate Mughal-style palace durbar hall.",
        "Ministers and sages presenting various rings and jewels to the king. The king shaking his head — none satisfy his request. A humble elderly craftsman stepping forward with a simple gold ring.",
        "Close-up of a simple gold band with tiny inscription inside. The king reading the inscription with wonder. Light reflecting off the ring. The inscription: 'This too shall pass.' Warm palace light.",
        "The king in two contrasting scenes — wearing the ring during times of sorrow (it gives him hope) and during times of joy (it gives him humility). Split composition showing both moods. The ring glowing on his finger.",
    ],
}


def generate_image(model, prompt: str, output_path: str, aspect_ratio: str = "3:4", max_retries: int = 8):
    full_prompt = STYLE_PREFIX + prompt

    for attempt in range(max_retries):
        try:
            response = model.generate_images(
                prompt=full_prompt,
                number_of_images=1,
                aspect_ratio=aspect_ratio,
            )
            if response.images:
                response.images[0].save(location=output_path)
                return True
            print(f"    ⚠️  Empty response, retrying...")
            time.sleep(30)
            continue
        except Exception as e:
            err = str(e)
            if "429" in err or "Quota" in err or "Resource exhausted" in err:
                wait = 45 * (attempt + 1)
                print(f"    ⏳ Rate limited, waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
            else:
                print(f"    ⚠️  Error: {err[:120]}, retrying in 30s...")
                time.sleep(30)
    return False


def update_story_json(story_id: str, image_ids: list[str]):
    """Update the story JSON to reference generated images."""
    en_path = os.path.join(EN_DIR, f"{story_id}.json")
    if not os.path.exists(en_path):
        return

    with open(en_path) as f:
        story = json.load(f)

    for i, section in enumerate(story["sections"]):
        if i < len(image_ids):
            section["image"] = image_ids[i]

    with open(en_path, "w") as f:
        json.dump(story, f, indent=2, ensure_ascii=False)
        f.write("\n")

    hi_path = os.path.join(HI_DIR, f"{story_id}.json")
    if os.path.exists(hi_path):
        with open(hi_path) as f:
            hi_story = json.load(f)
        for i, section in enumerate(hi_story["sections"]):
            if i < len(image_ids):
                section["image"] = image_ids[i]
        with open(hi_path, "w") as f:
            json.dump(hi_story, f, indent=2, ensure_ascii=False)
            f.write("\n")


def process_story(model, story_id: str, dry_run: bool = False):
    if story_id not in STORY_PROMPTS:
        print(f"  ⚠️  No prompts defined for {story_id}, skipping")
        return

    prompts = STORY_PROMPTS[story_id]
    image_ids = []
    slug = story_id.replace("puranic-", "").replace("epic-", "").replace("panchatantra-", "").replace("saint-", "").replace("vedic-", "").replace("wisdom-", "")

    for i, prompt in enumerate(prompts):
        image_id = f"{slug}-{i+1:02d}"
        image_ids.append(image_id)
        output_path = os.path.join(IMAGES_DIR, f"{image_id}.png")

        if os.path.exists(output_path):
            print(f"  ✓ {image_id}.png already exists, skipping")
            continue

        if dry_run:
            print(f"  [DRY RUN] Would generate {image_id}.png")
            continue

        print(f"  Generating {image_id}.png ...")
        try:
            success = generate_image(model, prompt, output_path)
            if success:
                print(f"  ✓ Saved {image_id}.png")
            else:
                print(f"  ✗ No image returned for {image_id}")
        except Exception as e:
            print(f"  ✗ Error generating {image_id}: {e}")
            time.sleep(2)
            continue

        time.sleep(0.5)

    if not dry_run:
        update_story_json(story_id, image_ids)
        print(f"  ✓ Updated {story_id} JSON with image references")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", help="Process a single story ID")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without actually generating")
    parser.add_argument("--list", action="store_true", help="List all stories that need images")
    args = parser.parse_args()

    if args.list:
        for sid in sorted(STORY_PROMPTS.keys()):
            count = len(STORY_PROMPTS[sid])
            en_path = os.path.join(EN_DIR, f"{sid}.json")
            has_images = False
            if os.path.exists(en_path):
                with open(en_path) as f:
                    d = json.load(f)
                has_images = any(s.get("image") for s in d["sections"])
            status = "HAS IMAGES" if has_images else "needs images"
            print(f"  {sid}: {count} prompts ({status})")
        total = sum(len(v) for v in STORY_PROMPTS.values())
        print(f"\nTotal: {len(STORY_PROMPTS)} stories, {total} images (~${total * 0.03:.2f})")
        return

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")

    os.makedirs(IMAGES_DIR, exist_ok=True)

    if args.story:
        print(f"Processing: {args.story}")
        process_story(model, args.story, dry_run=args.dry_run)
    else:
        stories = sorted(STORY_PROMPTS.keys())
        total = sum(len(STORY_PROMPTS[s]) for s in stories)
        print(f"Generating images for {len(stories)} stories ({total} images)")
        print(f"Estimated cost: ~${total * 0.03:.2f}\n")

        for sid in stories:
            print(f"\n{'='*60}")
            print(f"Story: {sid} ({len(STORY_PROMPTS[sid])} sections)")
            print(f"{'='*60}")
            process_story(model, sid, dry_run=args.dry_run)

    print("\nDone!")


if __name__ == "__main__":
    main()
