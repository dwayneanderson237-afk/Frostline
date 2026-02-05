import json
import os
import sqlite3
import smtplib
from functools import wraps
from email.message import EmailMessage

from flask import (
    Flask,
    render_template,
    abort,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response,
    send_from_directory,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["ADMIN_USERNAME"] = os.environ.get("ADMIN_USERNAME", "admin")
app.config["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD", "admin123")
app.config["SMTP_HOST"] = os.environ.get("SMTP_HOST", "")
app.config["SMTP_PORT"] = int(os.environ.get("SMTP_PORT", "587"))
app.config["SMTP_USER"] = os.environ.get("SMTP_USER", "")
app.config["SMTP_PASS"] = os.environ.get("SMTP_PASS", "")
app.config["SMTP_USE_TLS"] = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
app.config["SMTP_USE_SSL"] = os.environ.get("SMTP_USE_SSL", "false").lower() == "true"
app.config["SMTP_FROM"] = os.environ.get("SMTP_FROM", "info@frostlinecoons.com")
app.config["SMTP_TO"] = os.environ.get("SMTP_TO", "info@frostlinecoons.com")
app.config["RESERVATION_DEPOSIT"] = float(os.environ.get("RESERVATION_DEPOSIT", "300"))
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024
app.config["UPLOADS_PATH"] = os.environ.get(
    "UPLOADS_PATH", os.path.join(app.root_path, "static", "uploads")
)

DATABASE = os.environ.get(
    "DATABASE_PATH", os.path.join(app.root_path, "frostline_coons.db")
)
ALLOWED_KITTEN_IMAGE_EXTS = {".jpg", ".jpeg"}
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTS = {".mp4", ".webm", ".mov"}

# -------------------- DEFAULT CONTENT --------------------
DEFAULT_KITTENS = [
    {
        "id": 1,
        "name": "Luna",
        "age": 4,
        "gender": "Female",
        "personality": "Playful, affectionate",
        "price": 1200,
        "folder": "kitten01",
        "image_count": 3,
        "featured": True,
        "health_details": "Vaccinated, dewormed, microchipped. Healthy and active.",
        "color": "Black and white tuxedo",
        "coat": "Silky medium coat",
        "energy": "Playful",
        "good_with": ["Kids", "Gentle dogs", "Other cats"],
        "bio": "Confident and curious, Luna loves window perches and following you from room to room.",
        "highlights": [
            "Loves feather toys and wand play",
            "Litter trained and uses scratch posts",
            "Soft trilling purr when picked up"
        ]
    },
    {
        "id": 2,
        "name": "Leo",
        "age": 5,
        "gender": "Male",
        "personality": "Curious, friendly",
        "price": 1300,
        "folder": "leo",
        "image_count": 3,
        "featured": True,
        "health_details": "All health checks done. Very social and playful.",
        "color": "Brown tabby with white",
        "coat": "Fluffy, classic Maine Coon coat",
        "energy": "High",
        "good_with": ["Kids", "Active homes", "Other cats"],
        "bio": "Leo is outgoing and bold, always the first to greet visitors and investigate new toys.",
        "highlights": [
            "Big playful personality",
            "Enjoys climbing and tall perches",
            "Gentle, sociable temperament"
        ]
    },
    {
        "id": 3,
        "name": "Milo",
        "age": 3,
        "gender": "Male",
        "personality": "Gentle, cuddly",
        "price": 1100,
        "folder": "milo",
        "image_count": 3,
        "featured": True,
        "health_details": "Healthy, fully vaccinated, loves attention.",
        "color": "Black smoke",
        "coat": "Soft plush coat",
        "energy": "Calm",
        "good_with": ["Quiet homes", "Adults", "Calm cats"],
        "bio": "Milo is a lap-seeker with a mellow vibe who bonds quickly and loves slow head rubs.",
        "highlights": [
            "Excellent lap companion",
            "Quiet and steady temperament",
            "Very gentle with handling"
        ]
    },
    {
        "id": 4,
        "name": "Nala",
        "age": 6,
        "gender": "Female",
        "personality": "Independent, smart",
        "price": 1250,
        "folder": "kitten02",
        "image_count": 3,
        "featured": True,
        "health_details": "Excellent health, dewormed, microchipped.",
        "color": "Warm red tabby",
        "coat": "Thick, water-resistant coat",
        "energy": "Medium",
        "good_with": ["Adults", "Calm dogs", "Other cats"],
        "bio": "Nala is bright and composed, happiest when she has a cozy perch to survey her world.",
        "highlights": [
            "Quick learner with toys and puzzles",
            "Polite and tidy manners",
            "Affectionate on her terms"
        ]
    },
    {
        "id": 5,
        "name": "Simba",
        "age": 4,
        "gender": "Male",
        "personality": "Loyal, curious",
        "price": 1350,
        "folder": "kitten03",
        "image_count": 3,
        "featured": True,
        "health_details": "Fully vaccinated and monitored daily.",
        "color": "Silver tabby",
        "coat": "Shaggy, lion-like ruff",
        "energy": "Medium-high",
        "good_with": ["Kids", "Dogs", "Other cats"],
        "bio": "Simba is confident and playful, with a big heart and a gentle, steady presence.",
        "highlights": [
            "Loves interactive play",
            "Great with new environments",
            "Follows you like a shadow"
        ]
    },
    {
        "id": 6,
        "name": "Chloe",
        "age": 5,
        "gender": "Female",
        "personality": "Playful, loving",
        "price": 1400,
        "folder": "kitten04",
        "image_count": 3,
        "featured": True,
        "health_details": "Vaccinated, healthy, loves to cuddle.",
        "color": "Blue (gray) with white",
        "coat": "Silky and dense",
        "energy": "Playful",
        "good_with": ["Kids", "Other cats", "First-time owners"],
        "bio": "Chloe is a social butterfly who melts into your arms and loves gentle grooming.",
        "highlights": [
            "Very affectionate and people-focused",
            "Enjoys brushing and belly rubs",
            "Sweet, soft purrs"
        ]
    },
    {
        "id": 7,
        "name": "Oliver",
        "age": 3,
        "gender": "Male",
        "personality": "Friendly",
        "price": 1100,
        "folder": "kitten05",
        "image_count": 3,
        "featured": False,
        "health_details": "Healthy and playful.",
        "color": "Brown tabby",
        "coat": "Medium-long, fluffy coat",
        "energy": "High",
        "good_with": ["Kids", "Active homes", "Other cats"],
        "bio": "Oliver is the explorer of the group, always curious and happy to meet new people.",
        "highlights": [
            "Excellent play drive",
            "Confident and outgoing",
            "Quick to learn routines"
        ]
    },
    {
        "id": 8,
        "name": "Daisy",
        "age": 4,
        "gender": "Female",
        "personality": "Sweet",
        "price": 1150,
        "folder": "Kitten08",
        "image_count": 3,
        "featured": False,
        "health_details": "Vaccinated and energetic.",
        "color": "Cream tabby",
        "coat": "Soft, plush coat",
        "energy": "Medium",
        "good_with": ["Kids", "Calm dogs", "Other cats"],
        "bio": "Daisy is gentle and affectionate, happiest curled beside you or near a sunny window.",
        "highlights": [
            "Soft, quiet temperament",
            "Enjoys gentle play",
            "Very cuddly in the evenings"
        ]
    },
    {
        "id": 9,
        "name": "Max",
        "age": 5,
        "gender": "Male",
        "personality": "Curious",
        "price": 1200,
        "folder": "kitten01",
        "image_count": 3,
        "featured": False,
        "health_details": "Healthy, loves exploring.",
        "color": "Black and white",
        "coat": "Dense, weather-ready coat",
        "energy": "Medium-high",
        "good_with": ["Kids", "Other cats", "Active homes"],
        "bio": "Max is bold and inquisitive, always checking out new rooms and toys.",
        "highlights": [
            "Great confidence and curiosity",
            "Plays well with others",
            "Loves climbing"
        ]
    },
    {
        "id": 10,
        "name": "Lily",
        "age": 3,
        "gender": "Female",
        "personality": "Cuddly",
        "price": 1100,
        "folder": "kitten02",
        "image_count": 3,
        "featured": False,
        "health_details": "Friendly and vaccinated.",
        "color": "Red tabby with white",
        "coat": "Feathery long coat",
        "energy": "Calm",
        "good_with": ["Adults", "Quiet homes", "Other cats"],
        "bio": "Lily is serene and affectionate, preferring cozy spaces and gentle attention.",
        "highlights": [
            "A calm, soothing presence",
            "Loves lap time",
            "Very gentle with handling"
        ]
    },
    {
        "id": 11,
        "name": "Charlie",
        "age": 4,
        "gender": "Male",
        "personality": "Gentle",
        "price": 1250,
        "folder": "kitten03",
        "image_count": 3,
        "featured": False,
        "health_details": "Healthy, playful, loves humans.",
        "color": "Silver tabby",
        "coat": "Thick, plush coat",
        "energy": "Medium",
        "good_with": ["Kids", "Other cats", "First-time owners"],
        "bio": "Charlie is easygoing and affectionate, with a soft purr and a sweet nature.",
        "highlights": [
            "Balanced energy",
            "Affectionate and steady",
            "Great family companion"
        ]
    },
    {
        "id": 12,
        "name": "Bella",
        "age": 5,
        "gender": "Female",
        "personality": "Smart",
        "price": 1300,
        "folder": "kitten04",
        "image_count": 3,
        "featured": False,
        "health_details": "Vaccinated, curious, friendly.",
        "color": "Blue tortie",
        "coat": "Velvety, thick coat",
        "energy": "Medium-high",
        "good_with": ["Adults", "Kids", "Other cats"],
        "bio": "Bella is clever and curious, always interested in puzzle toys and new routines.",
        "highlights": [
            "Quick learner",
            "Playful and attentive",
            "Enjoys interactive toys"
        ]
    },
    {
        "id": 13,
        "name": "Oscar",
        "age": 3,
        "gender": "Male",
        "personality": "Playful",
        "price": 1100,
        "folder": "kitten05",
        "image_count": 3,
        "featured": False,
        "health_details": "Active and healthy.",
        "color": "Classic brown tabby",
        "coat": "Long, fluffy coat",
        "energy": "High",
        "good_with": ["Kids", "Active homes", "Other cats"],
        "bio": "Oscar is energetic and silly, always ready to chase a toy or hop onto a perch.",
        "highlights": [
            "Very playful and athletic",
            "Social and outgoing",
            "Loves wand toys"
        ]
    },
    {
        "id": 14,
        "name": "Mia",
        "age": 4,
        "gender": "Female",
        "personality": "Affectionate",
        "price": 1150,
        "folder": "kitten01",
        "image_count": 3,
        "featured": False,
        "health_details": "Vaccinated and loving.",
        "color": "Black and white",
        "coat": "Soft, silky coat",
        "energy": "Medium",
        "good_with": ["Kids", "Other cats", "Calm dogs"],
        "bio": "Mia is affectionate and steady, happy to curl up beside you at the end of the day.",
        "highlights": [
            "Very people-focused",
            "Gentle and patient",
            "Sweet, steady temperament"
        ]
    },
    {
        "id": 15,
        "name": "Jack",
        "age": 5,
        "gender": "Male",
        "personality": "Loyal",
        "price": 1200,
        "folder": "kitten02",
        "image_count": 3,
        "featured": False,
        "health_details": "Healthy and playful.",
        "color": "Red tabby",
        "coat": "Thick and fluffy",
        "energy": "Medium",
        "good_with": ["Kids", "Adults", "Other cats"],
        "bio": "Jack is calm and loyal, with a gentle presence and an affectionate personality.",
        "highlights": [
            "Easygoing and steady",
            "Great with families",
            "Enjoys relaxed play"
        ]
    },
    {
        "id": 16,
        "name": "Lucy",
        "age": 3,
        "gender": "Female",
        "personality": "Sweet",
        "price": 1100,
        "folder": "kitten03",
        "image_count": 3,
        "featured": False,
        "health_details": "Friendly and healthy.",
        "color": "Silver tabby with white",
        "coat": "Feathery long coat",
        "energy": "Calm",
        "good_with": ["Quiet homes", "Adults", "Other cats"],
        "bio": "Lucy is gentle and sweet, preferring calm spaces and soft, reassuring attention.",
        "highlights": [
            "Very calm temperament",
            "Loves quiet cuddles",
            "Great for relaxed homes"
        ]
    }
]

DEFAULT_TESTIMONIALS = [
    {
        "author": "Ava Martinez",
        "quote": "Our kitten arrived confident and social. The care and communication were incredible.",
        "image": "images/doherty.jpg"
    },
    {
        "author": "Jordan Wells",
        "quote": "Sweet temperament and beautiful coat. We felt supported from day one.",
        "image": "images/fluffy.jpg"
    },
    {
        "author": "Priya Mehta",
        "quote": "Healthy, playful, and already attached to our family. Best decision we made.",
        "image": "images/jack.jpg"
    },
    {
        "author": "Ethan Nguyen",
        "quote": "The most gentle kitten. Calm with kids and so easy to handle.",
        "image": "images/misty.jpg"
    },
    {
        "author": "Ella Carter",
        "quote": "The temperament matching was spot on. Our kitten fits us perfectly.",
        "image": "images/nono.jpg"
    },
    {
        "author": "Marcus Patel",
        "quote": "Clear health records and a smooth process. We felt confident the whole time.",
        "image": "images/kanashi-7NcdSLcRTq8-unsplash.jpg"
    },
    {
        "author": "Zoe Rivera",
        "quote": "Playful, affectionate, and incredibly smart. Our home feels complete now.",
        "image": "images/bee-felten-leidel-DkYlK2vyuZg-unsplash.jpg"
    },
    {
        "author": "Samira Khan",
        "quote": "The kitten settled in within days. Loving, curious, and full of personality.",
        "image": "images/bobbi-wu-UN6uVzke__g-unsplash.jpg"
    }
]

DEFAULT_SECTIONS = [
    {
        "key": "logo",
        "title": "Frostline Coons",
        "body": "",
        "image": ""
    },
    {
        "key": "hero",
        "title": "Frostline Coons",
        "body": (
            "A cattery built on patience, ethics, and devotion. "
            "We don’t rush kittens into the world — we raise companions for life."
        ),
        "image": "images/hero_kitten.jpg"
    },
    {
        "key": "hero_slide_2",
        "title": "Raised for Real Homes",
        "body": "Daily handling, gentle routines, and confident temperaments built from the very start.",
        "image": "images/hero_home.jpg"
    },
    {
        "key": "hero_slide_3",
        "title": "Safe Travel, Calm Arrivals",
        "body": "Thoughtful travel planning by ground or air, with comfort and communication throughout.",
        "image": "images/hero_delivery.jpg"
    },
    {
        "key": "story",
        "title": "Our Story",
        "body": (
            "Frostline Coons was never meant to be fast, loud, or commercial. "
            "It began quietly — with research, lineage study, late nights, "
            "and a refusal to cut corners. Every kitten carries intention. "
            "We raise in small, carefully planned litters so each kitten "
            "gets hands-on socialization from day one.\n\n"
            "Our foundation is built on transparency and care: we document "
            "every stage of growth, prioritize clean spaces, and focus on "
            "temperaments that thrive in real homes. We want families to "
            "meet a kitten whose personality already feels like a perfect fit."
        ),
        "image": "images/story.jpg"
    },
    {
        "key": "health",
        "title": "Health & Care",
        "body": (
            "Genetics tested. Vet monitored. Nutrition curated. "
            "We raise slowly so bodies grow strong and minds stay gentle. "
            "Each kitten receives a full wellness plan, early social training, "
            "and careful introductions to grooming and handling.\n\n"
            "We use premium, balanced nutrition and keep detailed records "
            "of milestones, vaccines, and behavioral development so you "
            "can feel confident from the first day home."
        ),
        "image": "images/health.jpg"
    },
    {
        "key": "mission",
        "title": "Our Mission",
        "body": (
            "To preserve the Maine Coon with honesty. "
            "To protect families from unethical breeding. "
            "To stand behind every kitten — for life. "
            "We place only when the match is right, with long-term support "
            "and guidance included.\n\n"
            "This is a lifelong promise to families and to the breed we love: "
            "thoughtful practices, ethical standards, and cats that are healthy, "
            "confident, and deeply social."
        ),
        "image": "images/mission.jpg"
    },
    {
        "key": "travel",
        "title": "How I Travel to You",
        "body": (
            "Flight Nanny | Hand-delivered in cabin with a dedicated caregiver.\n"
            "Air Cargo | Climate-controlled travel with direct flights when possible.\n"
            "Ground Nanny | Personal ground transport with comfort breaks built in.\n"
            "Owner Pickup | Meet at our cattery or a nearby airport for handoff."
        ),
        "image": ""
    },
    {
        "key": "health_check",
        "title": "Health Check & Guarantees",
        "body": (
            "Veterinary health exam\n"
            "Age-appropriate vaccinations\n"
            "Deworming schedule completed\n"
            "FIV/FeLV screening\n"
            "Health certificate (when required)\n"
            "Wellness records provided\n"
            "Early socialization and handling\n"
            "Nutrition plan and transition guide"
        ),
        "image": ""
    },
    {
        "key": "adoption_journey",
        "title": "Your Adoption Journey",
        "body": (
            "Choose & Reserve | Select your kitten and place a reservation.\n"
            "Prepare & Plan | We confirm timing, care checklist, and travel plan.\n"
            "Safe Delivery | Your kitten travels with updates and comfort care.\n"
            "Homecoming Support | We guide you through the first days at home."
        ),
        "image": ""
    }
]

DEFAULT_PAGES = [
    {
        "slug": "delivery",
        "title": "Delivery & Arrival",
        "meta_title": "Maine Coon Kitten Delivery | Frostline Coons",
        "meta_description": "Learn how our Maine Coon kittens travel safely by ground or air, from pickup to arrival at your home or airport.",
        "hero_title": "Delivery & Arrival",
        "hero_body": (
            "From pickup to your front door (or airport handoff), our process is structured, calm, and kitten-first. "
            "We offer safe ground transport and carefully coordinated air travel with clear communication at every step."
        ),
        "hero_image": "images/hero_delivery.jpg",
        "steps": [
            {
                "title": "Preparation",
                "body": "We confirm paperwork, vet records, and travel requirements. Each kitten travels with familiar bedding, hydration, and a calm routine."
            },
            {
                "title": "Safe Transport",
                "body": "Choose ground or air options. Both routes are climate controlled, monitored, and planned for gentle handling and rest breaks."
            },
            {
                "title": "Arrival Support",
                "body": "We guide you through the first 48 hours at home, including feeding, settling tips, and introductions to your space."
            }
        ],
        "blocks": [
            {
                "title": "Pickup & Preparation",
                "body": "Each journey begins with a calm pickup routine. Kittens receive a final wellness check, hydration, and a familiar scent item to reduce stress.",
                "image": "images/care.jpg",
                "layout": "left"
            },
            {
                "title": "Ground Transport",
                "body": "Ground transport is ideal for regional deliveries. Our carriers are temperature controlled and routed for minimal time on the road.",
                "image": "images/health2.jpg",
                "layout": "right"
            },
            {
                "title": "Air Transport & Airport Pickup",
                "body": "For longer distances, we coordinate air travel with trusted couriers and pet-safe airline policies with a smooth airport handoff.",
                "image": "images/her.jpg",
                "layout": "left"
            },
            {
                "title": "Arrival at Home",
                "body": "We recommend a quiet room for the first day with water, food, and a soft bed. Let your kitten explore slowly and set their pace.",
                "image": "images/hero_home.jpg",
                "layout": "right"
            }
        ],
        "cta_title": "Questions About Delivery?",
        "cta_body": "We’ll help you choose the best option for your location and timeline. Reach out and we’ll guide you from reservation to arrival.",
        "cta_label": "Contact Us",
        "cta_link": "mailto:info@frostlinecoons.com"
    },
    {
        "slug": "about",
        "title": "About Frostline Coons",
        "meta_title": "About Frostline Coons | Maine Coon Breeder",
        "meta_description": "Learn about Frostline Coons, our breeding philosophy, and the care we provide for every Maine Coon kitten.",
        "hero_title": "About Frostline Coons",
        "hero_body": (
            "We raise Maine Coons with patience, transparency, and deep respect for the breed. "
            "Every kitten is socialized, nurtured, and matched carefully to the right home."
        ),
        "hero_image": "images/story.jpg",
        "steps": [],
        "blocks": [
            {
                "title": "Our Philosophy",
                "body": (
                    "We focus on small, carefully planned litters so each kitten receives daily handling and enrichment. "
                    "Health testing, clear communication, and ethical practices guide every decision."
                ),
                "image": "images/mission.jpg",
                "layout": "left"
            },
            {
                "title": "Early Socialization",
                "body": (
                    "Kittens are introduced to grooming, gentle handling, and everyday household sounds early. "
                    "This helps them grow into calm, confident companions."
                ),
                "image": "images/health.jpg",
                "layout": "right"
            },
            {
                "title": "Lifelong Support",
                "body": (
                    "We stay connected with families after pickup or delivery. "
                    "From feeding tips to temperament guidance, we’re here for you."
                ),
                "image": "images/hero_home.jpg",
                "layout": "left"
            }
        ],
        "cta_title": "Want to Learn More?",
        "cta_body": "We’re happy to answer questions about temperament, care, and availability.",
        "cta_label": "Email Us",
        "cta_link": "mailto:info@frostlinecoons.com"
    },
    {
        "slug": "faqs",
        "title": "Frequently Asked Questions",
        "meta_title": "Maine Coon FAQs | Frostline Coons",
        "meta_description": "Answers to common questions about Maine Coon kittens, care routines, and our adoption process.",
        "hero_title": "Frequently Asked Questions",
        "hero_body": (
            "Everything you need to know about our process, kitten care, and delivery options."
        ),
        "hero_image": "images/health2.jpg",
        "steps": [],
        "blocks": [
            {
                "title": "When do kittens go home?",
                "body": (
                    "Kittens typically go home after they are fully weaned, socialized, and cleared by the vet. "
                    "We prioritize health and confidence over speed."
                ),
                "image": "images/care.jpg",
                "layout": "left"
            },
            {
                "title": "Do you offer delivery?",
                "body": (
                    "Yes. We provide ground transport and air travel options depending on location and timing. "
                    "All deliveries are planned with the kitten’s comfort in mind."
                ),
                "image": "images/hero_delivery.jpg",
                "layout": "right"
            },
            {
                "title": "How do I prepare my home?",
                "body": (
                    "Set up a quiet starter room with food, water, litter, and a cozy bed. "
                    "We provide a transition guide with each kitten."
                ),
                "image": "images/hero_home.jpg",
                "layout": "left"
            }
        ],
        "cta_title": "Still Have Questions?",
        "cta_body": "Reach out and we’ll guide you through the next steps.",
        "cta_label": "Contact Us",
        "cta_link": "mailto:info@frostlinecoons.com"
    },
    {
        "slug": "contact",
        "title": "Contact Frostline Coons",
        "meta_title": "Contact Frostline Coons | Maine Coon Kittens",
        "meta_description": "Get in touch with Frostline Coons for availability, delivery questions, and kitten care guidance.",
        "hero_title": "Contact Frostline Coons",
        "hero_body": (
            "We respond quickly and personally. Tell us about your home, your timeline, and the kitten you’re looking for."
        ),
        "hero_image": "images/hero_kitten.jpg",
        "steps": [],
        "blocks": [
            {
                "title": "Email",
                "body": "info@frostlinecoons.com — We respond within 24–48 hours.",
                "image": "images/about1.jpg",
                "layout": "left"
            },
            {
                "title": "Delivery Questions",
                "body": "Let us know your location and preferred timing. We’ll recommend the safest transport option.",
                "image": "images/hero_delivery.jpg",
                "layout": "right"
            }
        ],
        "cta_title": "Ready to Start?",
        "cta_body": "Send a message and we’ll help you find the right kitten.",
        "cta_label": "Email Us",
        "cta_link": "mailto:info@frostlinecoons.com"
    }
]

DEFAULT_BLOG_POSTS = [
    {
        "title": "Maine Coon Temperament: What to Expect at Home",
        "excerpt": "Meet the gentle giant personality Maine Coons are known for, plus how to support their social, loyal nature at home.",
        "content": (
            "Maine Coons are famous for their calm, people‑oriented temperament. They tend to follow family members from room to room, "
            "communicating with soft chirps and trills rather than loud meows.\n\n"
            "Most Maine Coons enjoy being near you without demanding constant attention. They’re affectionate but independent, "
            "making them a great fit for busy homes that still want a bonded companion.\n\n"
            "To bring out their best personality, focus on daily interactive play, predictable routines, and gentle handling."
        ),
        "meta_title": "Maine Coon Temperament Guide | Frostline Coons",
        "meta_description": "Learn what the Maine Coon temperament is really like, from their affectionate nature to how they bond with families.",
        "keywords": "Maine Coon temperament, Maine Coon personality, gentle giant cat",
        "cover_image": "images/hero_kitten.jpg"
    },
    {
        "title": "How Big Do Maine Coons Get? Growth Stages Explained",
        "excerpt": "A clear look at Maine Coon growth stages, how long they take to mature, and how to support healthy development.",
        "content": (
            "Maine Coons grow more slowly than most breeds, often maturing over 3–5 years. It’s normal for them to look lanky "
            "in the early months before they fill out.\n\n"
            "Healthy growth depends on balanced nutrition, joint‑friendly activity, and consistent vet care. Avoid overfeeding, "
            "and aim for steady weight gain rather than sudden jumps.\n\n"
            "Your kitten’s growth rate will vary by genetics and lifestyle, but patience is key — the gentle giant takes time."
        ),
        "meta_title": "Maine Coon Size & Growth | Frostline Coons",
        "meta_description": "Discover how big Maine Coons get and what their growth timeline looks like from kitten to adult.",
        "keywords": "Maine Coon size, Maine Coon growth, how big do Maine Coons get",
        "cover_image": "images/story.jpg"
    },
    {
        "title": "Maine Coon Grooming Routine: Brushes, Baths, and Mats",
        "excerpt": "Keep the coat healthy and tangle‑free with a simple grooming routine built for Maine Coons.",
        "content": (
            "A Maine Coon’s coat is long, plush, and designed to shed — so gentle, regular grooming is essential. "
            "Use a wide‑tooth comb for the undercoat and a slicker brush for the topcoat.\n\n"
            "Focus on friction areas like the chest, belly, and behind the legs. Short, calm sessions work best, "
            "especially for kittens learning the routine.\n\n"
            "Baths are rarely needed, but an occasional warm bath can help during seasonal sheds or after messy adventures."
        ),
        "meta_title": "Maine Coon Grooming Tips | Frostline Coons",
        "meta_description": "Learn the best grooming routine for Maine Coons, including brushing tools, mat prevention, and bath tips.",
        "keywords": "Maine Coon grooming, Maine Coon brush, long-haired cat grooming",
        "cover_image": "images/health.jpg"
    },
    {
        "title": "Kitten‑Proofing Your Home for a Maine Coon",
        "excerpt": "Prepare your home for a curious, climbing kitten with practical, safety‑first tips.",
        "content": (
            "Maine Coon kittens are bold explorers. Secure cords, remove small swallowable items, and block off tight hiding spaces.\n\n"
            "Provide safe vertical spaces like sturdy cat trees and wall shelves so your kitten can climb without risk.\n\n"
            "A calm starter room helps ease the transition and prevents overstimulation during the first few days."
        ),
        "meta_title": "Kitten Proofing for Maine Coons | Frostline Coons",
        "meta_description": "Make your home safe for a Maine Coon kitten with simple, effective kitten‑proofing strategies.",
        "keywords": "kitten proofing, Maine Coon kitten home, cat safety tips",
        "cover_image": "images/hero_home.jpg"
    },
    {
        "title": "Feeding a Maine Coon Kitten: Schedule and Nutrition Tips",
        "excerpt": "A balanced feeding plan to support steady growth, strong joints, and a healthy coat.",
        "content": (
            "Maine Coon kittens need nutrient‑dense meals divided into smaller feedings throughout the day. "
            "Quality protein is essential for growth and muscle development.\n\n"
            "Look for kitten‑specific formulas with balanced calcium and phosphorus to support bone growth. "
            "Avoid rapid weight gain by keeping portions consistent.\n\n"
            "Hydration matters too — encourage water intake with fresh bowls and occasional wet food."
        ),
        "meta_title": "Maine Coon Kitten Feeding Guide | Frostline Coons",
        "meta_description": "Learn how to feed a Maine Coon kitten with the right schedule, portions, and nutrition for healthy growth.",
        "keywords": "Maine Coon kitten food, feeding schedule, Maine Coon nutrition",
        "cover_image": "images/health2.jpg"
    },
    {
        "title": "Maine Coon vs. Other Breeds: Is the Gentle Giant Right for You?",
        "excerpt": "Compare Maine Coons with other popular breeds to see if their temperament and needs fit your home.",
        "content": (
            "Maine Coons are known for their relaxed, friendly nature and large size. They often enjoy social homes "
            "and do best with space to climb and explore.\n\n"
            "Compared to more independent breeds, Maine Coons are more likely to greet guests and follow family members "
            "throughout the day.\n\n"
            "If you want a calm, affectionate, and interactive cat, the Maine Coon is an excellent choice."
        ),
        "meta_title": "Maine Coon vs Other Cats | Frostline Coons",
        "meta_description": "See how Maine Coons compare to other cat breeds and decide if the gentle giant is right for your home.",
        "keywords": "Maine Coon vs, gentle giant cat, best family cat",
        "cover_image": "images/mission.jpg"
    },
    {
        "title": "Introducing a Maine Coon to Dogs",
        "excerpt": "A calm, step‑by‑step approach to building trust between your kitten and dog.",
        "content": (
            "Start with scent swapping before any face‑to‑face introductions. Let your Maine Coon explore in a safe room "
            "while your dog gets used to the new scent.\n\n"
            "Use leashes and baby gates for gradual visual introductions. Keep sessions short and positive.\n\n"
            "With patience and consistent routines, many Maine Coons bond well with gentle dogs."
        ),
        "meta_title": "Maine Coon and Dog Introductions | Frostline Coons",
        "meta_description": "Learn how to safely introduce a Maine Coon kitten to a dog using calm, positive steps.",
        "keywords": "Maine Coon with dogs, introducing cats to dogs, kitten dog introduction",
        "cover_image": "images/her.jpg"
    },
    {
        "title": "Litter Training Tips for Maine Coon Kittens",
        "excerpt": "Make litter training simple with the right box size, litter type, and routine.",
        "content": (
            "Maine Coon kittens do best with large, low‑entry litter boxes that match their size. "
            "Place boxes in quiet, easy‑to‑reach areas.\n\n"
            "Stick to unscented, fine‑grained litter at first and keep the box exceptionally clean. "
            "Consistency is the key to reliable habits.\n\n"
            "If accidents happen, stay calm and gently redirect — most kittens learn quickly with routine."
        ),
        "meta_title": "Maine Coon Litter Training | Frostline Coons",
        "meta_description": "Easy litter training tips for Maine Coon kittens, including box size, litter type, and routines.",
        "keywords": "Maine Coon litter training, kitten litter tips, cat litter box size",
        "cover_image": "images/care.jpg"
    },
    {
        "title": "Understanding Maine Coon Coat Colors and Patterns",
        "excerpt": "From tabby to smoke, learn how Maine Coon colors are described and what to expect as they grow.",
        "content": (
            "Maine Coon colors range from classic tabby patterns to solid, smoke, and bi‑color coats. "
            "Kittens often change tone as their coat develops.\n\n"
            "Pattern names describe distribution: mackerel, classic, spotted, or ticked. "
            "A kitten’s adult coat typically appears after the first major shed.\n\n"
            "Color is purely cosmetic, but it’s fun to follow how their look evolves over time."
        ),
        "meta_title": "Maine Coon Colors & Patterns | Frostline Coons",
        "meta_description": "Learn the most common Maine Coon coat colors and patterns, and how they develop as kittens grow.",
        "keywords": "Maine Coon colors, Maine Coon patterns, tabby Maine Coon",
        "cover_image": "images/doherty.jpg"
    },
    {
        "title": "Maine Coon Health: Screening, Vet Visits, and Common Questions",
        "excerpt": "A practical overview of wellness checks, genetic screening, and routine care for Maine Coons.",
        "content": (
            "Responsible breeders prioritize genetic screening and early wellness checks. "
            "Routine vet visits help detect issues early and keep kittens on track.\n\n"
            "Ask about health records, vaccination schedules, and parasite prevention. "
            "These basics protect your kitten during the most sensitive stages.\n\n"
            "Consistent care creates a foundation for a long, healthy life."
        ),
        "meta_title": "Maine Coon Health & Vet Care | Frostline Coons",
        "meta_description": "Learn about health screening, vet schedules, and common questions for Maine Coon kitten care.",
        "keywords": "Maine Coon health, cat vet schedule, kitten wellness",
        "cover_image": "images/health.jpg"
    },
    {
        "title": "How to Travel Safely with a Maine Coon",
        "excerpt": "Whether it’s a vet visit or a longer trip, here’s how to keep travel calm and stress‑free.",
        "content": (
            "Start by making the carrier a positive space with familiar bedding and treats. "
            "Short practice rides can reduce travel anxiety.\n\n"
            "During travel, keep the carrier level and secure. "
            "Avoid loud music and sudden temperature changes.\n\n"
            "A calm routine and gentle handling make travel much easier for sensitive kittens."
        ),
        "meta_title": "Travel Tips for Maine Coons | Frostline Coons",
        "meta_description": "Safe travel tips for Maine Coon kittens, from carrier training to stress‑free rides.",
        "keywords": "Maine Coon travel, kitten carrier training, cat travel tips",
        "cover_image": "images/hero_delivery.jpg"
    },
    {
        "title": "Playtime and Enrichment for Smart, Active Maine Coons",
        "excerpt": "Keep your Maine Coon engaged with enrichment ideas that match their intelligence and energy.",
        "content": (
            "Maine Coons are curious and intelligent. Daily interactive play keeps them mentally stimulated and physically fit.\n\n"
            "Rotate toys, use puzzle feeders, and offer climbing opportunities to prevent boredom.\n\n"
            "A consistent play routine strengthens the bond and supports healthy development."
        ),
        "meta_title": "Maine Coon Enrichment Ideas | Frostline Coons",
        "meta_description": "Best enrichment ideas for Maine Coons: play routines, puzzle toys, and climbing setups.",
        "keywords": "Maine Coon toys, cat enrichment, Maine Coon playtime",
        "cover_image": "images/jddh.jpg"
    },
    {
        "title": "Harness Training a Maine Coon: Step‑by‑Step",
        "excerpt": "Teach leash skills the gentle way with short sessions and positive reinforcement.",
        "content": (
            "Start with a well‑fitting harness and let your Maine Coon sniff and explore it first. "
            "Reward calm behavior with treats.\n\n"
            "Keep early sessions indoors and short. Once comfortable, introduce the leash and practice gentle guidance.\n\n"
            "When your kitten moves confidently, try quiet outdoor areas for short, supervised walks."
        ),
        "meta_title": "Maine Coon Harness Training | Frostline Coons",
        "meta_description": "Learn how to harness train a Maine Coon with gentle, step‑by‑step guidance.",
        "keywords": "Maine Coon harness, leash training cat, cat walking tips",
        "cover_image": "images/kanashi-7NcdSLcRTq8-unsplash.jpg"
    },
    {
        "title": "The First Week Home: A Calm Transition Plan",
        "excerpt": "Help your kitten settle in with a simple routine that builds trust and confidence.",
        "content": (
            "Begin with a quiet room that includes food, water, litter, and a cozy bed. "
            "Let your kitten explore at their own pace.\n\n"
            "Maintain a consistent feeding and play schedule to reduce stress. "
            "Short, gentle play sessions help build confidence.\n\n"
            "Within a week, most Maine Coons are ready to explore more of the home."
        ),
        "meta_title": "First Week with a Maine Coon Kitten | Frostline Coons",
        "meta_description": "A calm, practical plan for the first week with your Maine Coon kitten.",
        "keywords": "first week kitten, Maine Coon transition, new kitten tips",
        "cover_image": "images/hero_home.jpg"
    },
    {
        "title": "Maine Coon Vocalizations: Chirps, Trills, and Communication",
        "excerpt": "Understand the gentle sounds Maine Coons use to connect with their humans.",
        "content": (
            "Maine Coons often communicate with soft chirps and trills instead of loud meows. "
            "These sounds are friendly signals, not demands.\n\n"
            "You’ll hear different tones for greetings, attention, or play. "
            "With time, you’ll learn your kitten’s unique language.\n\n"
            "Responding calmly helps build trust and a strong bond."
        ),
        "meta_title": "Maine Coon Sounds & Communication | Frostline Coons",
        "meta_description": "Learn what Maine Coon chirps and trills mean and how they communicate with families.",
        "keywords": "Maine Coon vocalizations, cat chirps, Maine Coon sounds",
        "cover_image": "images/fluffy.jpg"
    },
    {
        "title": "Managing Shedding: Seasonal Coat Care",
        "excerpt": "Reduce shedding and keep the coat healthy through seasonal grooming.",
        "content": (
            "Maine Coons shed more during seasonal changes. Increase brushing frequency during spring and fall.\n\n"
            "Use a wide‑tooth comb first, then finish with a slicker brush for the topcoat. "
            "Keep sessions short and calm.\n\n"
            "A balanced diet and hydration also support a healthy coat and reduced shedding."
        ),
        "meta_title": "Maine Coon Shedding Guide | Frostline Coons",
        "meta_description": "Seasonal grooming tips to manage Maine Coon shedding and keep the coat healthy.",
        "keywords": "Maine Coon shedding, cat grooming tips, seasonal coat care",
        "cover_image": "images/health2.jpg"
    },
    {
        "title": "Ideal Home Setup: Litter, Scratching, and Climbing",
        "excerpt": "Create a home environment that matches a Maine Coon’s size and curiosity.",
        "content": (
            "Large litter boxes, sturdy scratching posts, and tall cat trees are essentials for Maine Coons. "
            "They need space to stretch and climb.\n\n"
            "Offer multiple scratching textures to protect furniture. "
            "Place climbing areas near windows for enrichment.\n\n"
            "A well‑set home environment keeps your cat confident and relaxed."
        ),
        "meta_title": "Best Home Setup for Maine Coons | Frostline Coons",
        "meta_description": "Build the ideal home setup for a Maine Coon with litter, scratching, and climbing essentials.",
        "keywords": "Maine Coon home setup, cat tree for Maine Coon, litter box size",
        "cover_image": "images/mission.jpg"
    },
    {
        "title": "Socializing Maine Coon Kittens with Kids",
        "excerpt": "Teach gentle handling and build a safe, positive relationship between kids and kittens.",
        "content": (
            "Start with short, supervised interactions. Teach children to use calm voices and gentle hands.\n\n"
            "Reward your kitten for calm behavior and give them plenty of breaks. "
            "A safe retreat space prevents overstimulation.\n\n"
            "With patience, Maine Coons often become wonderful family companions."
        ),
        "meta_title": "Maine Coon Kittens and Kids | Frostline Coons",
        "meta_description": "How to socialize Maine Coon kittens with kids safely and build a lasting bond.",
        "keywords": "Maine Coon kids, kitten socialization, family cat",
        "cover_image": "images/doherty.jpg"
    },
    {
        "title": "Nighttime Routine: Helping Your Kitten Sleep Through the Night",
        "excerpt": "A practical bedtime routine that supports calm nights for you and your kitten.",
        "content": (
            "End the day with a play‑and‑feed routine to help your kitten settle. "
            "A small meal after play encourages sleepiness.\n\n"
            "Keep the bedroom quiet and avoid overstimulation before bed. "
            "Consistency helps kittens learn the nighttime rhythm.\n\n"
            "Within a few weeks, most kittens adapt to a stable sleep routine."
        ),
        "meta_title": "Kitten Nighttime Routine | Frostline Coons",
        "meta_description": "Help your Maine Coon kitten sleep through the night with a gentle, consistent routine.",
        "keywords": "kitten sleep routine, Maine Coon nighttime, kitten bedtime tips",
        "cover_image": "images/hero_home.jpg"
    },
    {
        "title": "Choosing the Right Maine Coon Breeder: Red Flags and Green Flags",
        "excerpt": "Know what to look for in ethical breeding practices and transparent communication.",
        "content": (
            "A responsible breeder provides health records, clear communication, and a clean environment. "
            "They should be transparent about lineage and care routines.\n\n"
            "Red flags include rushed timelines, no vet documentation, or pressure to buy quickly.\n\n"
            "Choose a breeder who prioritizes the kitten’s welfare and long‑term support."
        ),
        "meta_title": "Choosing a Maine Coon Breeder | Frostline Coons",
        "meta_description": "Learn how to identify ethical Maine Coon breeders and avoid common red flags.",
        "keywords": "Maine Coon breeder, ethical breeders, buying a Maine Coon",
        "cover_image": "images/story.jpg"
    },
    {
        "title": "Maine Coon Lifespan and Senior Care",
        "excerpt": "Support your Maine Coon through every life stage with gentle, proactive care.",
        "content": (
            "Maine Coons can live long, healthy lives with proper nutrition and routine vet visits. "
            "As they age, they may need softer bedding and lower climbing options.\n\n"
            "Senior diets and joint support can help maintain comfort and mobility. "
            "Regular checkups are essential for early detection.\n\n"
            "A calm home environment and daily affection make the senior years rewarding."
        ),
        "meta_title": "Maine Coon Lifespan & Senior Care | Frostline Coons",
        "meta_description": "Learn how to care for Maine Coons as they age, including diet, comfort, and routine vet care.",
        "keywords": "Maine Coon lifespan, senior cat care, Maine Coon aging",
        "cover_image": "images/health.jpg"
    },
    {
        "title": "Water Play and Curiosity: Safe Ways to Encourage It",
        "excerpt": "Many Maine Coons love water — here’s how to make it fun and safe.",
        "content": (
            "Some Maine Coons are fascinated by water. Provide shallow bowls or trickling fountains for safe exploration.\n\n"
            "Never force water play. Let curiosity lead and reward gentle investigation with praise or treats.\n\n"
            "Short, supervised sessions keep water play safe and enjoyable."
        ),
        "meta_title": "Maine Coon Water Play | Frostline Coons",
        "meta_description": "Safe ways to encourage Maine Coon water play without stress or forcing.",
        "keywords": "Maine Coon water play, cat fountains, curious cats",
        "cover_image": "images/bee-felten-leidel-DkYlK2vyuZg-unsplash.jpg"
    },
    {
        "title": "Introducing Two Cats: A Gentle Maine Coon Plan",
        "excerpt": "A slow, scent‑first introduction method that builds confidence and reduces stress.",
        "content": (
            "Start with scent swapping and separate spaces for each cat. "
            "Allow them to explore each other’s space without direct contact.\n\n"
            "Use short, calm visual introductions with a barrier. "
            "Keep sessions positive and end on a good note.\n\n"
            "With patience, most cats adjust and learn to coexist peacefully."
        ),
        "meta_title": "Introducing Cats to a Maine Coon | Frostline Coons",
        "meta_description": "Learn a calm, step‑by‑step process for introducing a Maine Coon to another cat.",
        "keywords": "introducing cats, Maine Coon with other cats, cat introduction tips",
        "cover_image": "images/kanashi-h08T7bg4D5E-unsplash.jpg"
    },
    {
        "title": "Microchipping and Identification Essentials",
        "excerpt": "Protect your kitten with reliable identification and updated records.",
        "content": (
            "Microchipping is a permanent form of identification. "
            "Be sure to register the chip and keep contact info updated.\n\n"
            "Breakaway collars with ID tags can add an extra layer of safety. "
            "For indoor cats, microchipping is still strongly recommended.\n\n"
            "Simple identification steps can make a big difference if a cat is ever lost."
        ),
        "meta_title": "Microchipping Maine Coon Kittens | Frostline Coons",
        "meta_description": "Learn why microchipping and ID tags matter for Maine Coon kittens and how to keep records updated.",
        "keywords": "microchipping cats, Maine Coon identification, cat safety",
        "cover_image": "images/jack.jpg"
    },
    {
        "title": "How to Read a Vet Health Record for Your Kitten",
        "excerpt": "Understand the basics of vaccination records, deworming notes, and wellness checks.",
        "content": (
            "A kitten health record typically includes vaccination dates, deworming schedules, and vet exam notes. "
            "Ask your breeder to walk you through any unfamiliar terms.\n\n"
            "Look for consistent dates and clear documentation. "
            "Keep these records organized for future vet visits.\n\n"
            "Clear health records give you confidence in your kitten’s early care."
        ),
        "meta_title": "Reading Kitten Health Records | Frostline Coons",
        "meta_description": "Learn how to read and understand your Maine Coon kitten’s vet health records and vaccine schedule.",
        "keywords": "kitten health records, cat vaccines, Maine Coon vet care",
        "cover_image": "images/health.jpg"
    },
    {
        "title": "Maine Coon Personality Types: Finding the Right Match",
        "excerpt": "Every kitten is unique — here’s how to match personality with your household.",
        "content": (
            "Some Maine Coons are playful and bold, while others are calm and reserved. "
            "Ask about temperament observations and daily routines.\n\n"
            "Consider your household’s energy level. A quieter home may pair best with a gentle kitten, "
            "while active families often enjoy a playful companion.\n\n"
            "Matching personality ensures a smoother transition for both kitten and family."
        ),
        "meta_title": "Maine Coon Personality Match | Frostline Coons",
        "meta_description": "How to match Maine Coon kitten personalities to your home, lifestyle, and family.",
        "keywords": "Maine Coon personality, choosing a kitten, kitten temperament",
        "cover_image": "images/misty.jpg"
    },
    {
        "title": "Seasonal Care: Keeping Your Maine Coon Comfortable Year‑Round",
        "excerpt": "Adjust grooming, hydration, and indoor comfort across seasons.",
        "content": (
            "In warmer months, increase brushing to reduce shedding and keep your Maine Coon cool. "
            "Provide shade, fresh water, and air circulation.\n\n"
            "During colder months, maintain warmth and check for dry skin. "
            "Consistent grooming prevents mats from forming.\n\n"
            "Small seasonal adjustments keep your cat comfortable and healthy."
        ),
        "meta_title": "Seasonal Maine Coon Care | Frostline Coons",
        "meta_description": "Seasonal tips for Maine Coon care, including grooming, hydration, and comfort.",
        "keywords": "Maine Coon seasonal care, cat grooming tips, winter cat care",
        "cover_image": "images/hero_home.jpg"
    },
    {
        "title": "Indoor vs. Outdoor: Safe Options for Maine Coons",
        "excerpt": "Explore safe ways to provide outdoor time without sacrificing safety.",
        "content": (
            "Indoor living is the safest option for Maine Coons, but enrichment matters. "
            "Add window perches, climbing structures, and interactive play.\n\n"
            "If you want outdoor time, consider a secure catio or harness training. "
            "Supervised time outdoors reduces risk.\n\n"
            "A safe environment keeps your cat healthy while still meeting their curiosity."
        ),
        "meta_title": "Indoor vs Outdoor Maine Coon | Frostline Coons",
        "meta_description": "Learn safe indoor and outdoor options for Maine Coons, including catios and harness training.",
        "keywords": "indoor Maine Coon, catio, outdoor cat safety",
        "cover_image": "images/kanashi-7NcdSLcRTq8-unsplash.jpg"
    },
    {
        "title": "Understanding Maine Coon Play Styles and Toy Choices",
        "excerpt": "Pick toys that match your Maine Coon’s natural instincts and energy level.",
        "content": (
            "Maine Coons love interactive toys like feather wands, crinkle balls, and puzzle feeders. "
            "Rotate toys to keep interest high.\n\n"
            "Many enjoy chasing and climbing, so tall cat trees and tunnels are great additions.\n\n"
            "Daily play supports healthy weight and strong bonds with your family."
        ),
        "meta_title": "Maine Coon Toys & Play | Frostline Coons",
        "meta_description": "Best toy ideas and play styles for Maine Coons to keep them active and happy.",
        "keywords": "Maine Coon toys, cat play styles, interactive cat toys",
        "cover_image": "images/nono.jpg"
    },
    {
        "title": "Preparing for Delivery Day: From Carrier to First Cuddle",
        "excerpt": "A practical checklist for delivery day, whether your kitten arrives by ground or air.",
        "content": (
            "Prepare a quiet room with food, water, and litter before arrival. "
            "Have a comfortable carrier ready for safe transport home.\n\n"
            "Keep the environment calm and limit visitors on day one. "
            "Let your kitten explore at their own pace.\n\n"
            "The first cuddles come naturally once your kitten feels safe and settled."
        ),
        "meta_title": "Delivery Day Checklist | Frostline Coons",
        "meta_description": "Prepare for Maine Coon kitten delivery day with a calm, practical checklist.",
        "keywords": "kitten delivery day, Maine Coon arrival, new kitten checklist",
        "cover_image": "images/hero_delivery.jpg"
    },
    {
        "title": "Maine Coon Coat Care: Preventing Mats in Long Fur",
        "excerpt": "Learn how to prevent mats with the right tools, routine, and handling.",
        "content": (
            "Long coats are prone to matting around the chest, belly, and tail base. "
            "Brush gently in short sessions to avoid pulling.\n\n"
            "Use a wide‑tooth comb to detangle and follow with a slicker brush. "
            "Focus on friction areas during seasonal sheds.\n\n"
            "Consistent grooming keeps the coat comfortable and healthy."
        ),
        "meta_title": "Preventing Maine Coon Mats | Frostline Coons",
        "meta_description": "Prevent matting in Maine Coon coats with easy grooming tips and the right tools.",
        "keywords": "Maine Coon mats, grooming long hair cats, cat coat care",
        "cover_image": "images/health2.jpg"
    },
    {
        "title": "Best Litter Box Setup for Large Cats",
        "excerpt": "Large cats need large boxes — here’s how to set up a comfortable litter area.",
        "content": (
            "Maine Coons are bigger than most breeds, so standard litter boxes often feel cramped. "
            "Choose oversized boxes with low entry for easy access.\n\n"
            "Place boxes in quiet, low‑traffic areas and keep them very clean. "
            "Many cats prefer unscented clumping litter.\n\n"
            "A comfortable setup encourages consistent habits and reduces stress."
        ),
        "meta_title": "Litter Box Setup for Maine Coons | Frostline Coons",
        "meta_description": "Create the perfect litter box setup for large Maine Coon cats with practical tips.",
        "keywords": "large cat litter box, Maine Coon litter setup, litter box tips",
        "cover_image": "images/jddh.jpg"
    },
    {
        "title": "Maine Coon Vaccination Schedule: What to Know",
        "excerpt": "Understand the basics of kitten vaccines and why timing matters.",
        "content": (
            "Kittens receive a series of core vaccines during their first months. "
            "Your vet will provide a schedule based on age and health status.\n\n"
            "Follow recommended timelines to maintain protection during early development. "
            "Keep records organized for future visits.\n\n"
            "If you travel or board your cat, vaccines may be required by facilities."
        ),
        "meta_title": "Maine Coon Vaccine Schedule | Frostline Coons",
        "meta_description": "A simple overview of kitten vaccines and what to expect for Maine Coons.",
        "keywords": "kitten vaccines, Maine Coon vaccination, cat vaccine schedule",
        "cover_image": "images/health.jpg"
    },
    {
        "title": "How to Build Trust with a New Maine Coon Kitten",
        "excerpt": "Gentle routines and patience help your kitten feel safe and bonded.",
        "content": (
            "Trust grows through consistency. Offer food, play, and calm interaction at the same times each day.\n\n"
            "Use slow blinks and a soft voice. Let your kitten initiate contact rather than forcing cuddles.\n\n"
            "With a steady routine, most Maine Coons become deeply affectionate."
        ),
        "meta_title": "Building Trust with Maine Coon Kittens | Frostline Coons",
        "meta_description": "Learn how to build trust with a new Maine Coon kitten using calm routines and gentle handling.",
        "keywords": "Maine Coon kitten trust, bonding with kittens, new kitten tips",
        "cover_image": "images/luna.jpg"
    },
    {
        "title": "Maine Coon Shedding vs. Matting: What’s Normal?",
        "excerpt": "Understand the difference between normal shedding and coat issues that need attention.",
        "content": (
            "Shedding is normal for Maine Coons, especially during seasonal changes. "
            "Regular brushing keeps loose hair under control.\n\n"
            "Matting is different — it’s tangled fur that can pull on the skin. "
            "Focus on friction areas and use a comb to prevent mats.\n\n"
            "If mats form, handle them gently and consider professional grooming support."
        ),
        "meta_title": "Maine Coon Shedding vs Matting | Frostline Coons",
        "meta_description": "Learn the difference between normal Maine Coon shedding and coat matting issues.",
        "keywords": "Maine Coon shedding, cat matting, grooming tips",
        "cover_image": "images/fluffy.jpg"
    },
    {
        "title": "Maine Coon Playtime Schedule: How Much Is Enough?",
        "excerpt": "A realistic daily play routine that supports healthy energy and bonding.",
        "content": (
            "Aim for two to three short play sessions per day. "
            "Interactive play with wand toys helps satisfy hunting instincts.\n\n"
            "End sessions with a calm treat or meal to help your kitten settle.\n\n"
            "Consistent play reduces boredom and supports healthy behavior."
        ),
        "meta_title": "Maine Coon Playtime Routine | Frostline Coons",
        "meta_description": "How much playtime Maine Coon kittens need each day and how to structure sessions.",
        "keywords": "Maine Coon playtime, kitten play schedule, cat enrichment",
        "cover_image": "images/leo.jpg"
    },
    {
        "title": "Preparing Your Home for a Maine Coon’s First Winter",
        "excerpt": "Simple ways to keep your kitten cozy, hydrated, and comfortable in colder months.",
        "content": (
            "Keep bedding warm and away from drafts. "
            "Add cozy blankets and maintain a consistent indoor temperature.\n\n"
            "Monitor hydration in winter — heated homes can cause dryness. "
            "Fresh water and occasional wet food help balance it.\n\n"
            "Grooming remains important even in winter to keep the coat healthy."
        ),
        "meta_title": "Maine Coon Winter Care | Frostline Coons",
        "meta_description": "Winter care tips for Maine Coon kittens, including warmth, hydration, and coat care.",
        "keywords": "Maine Coon winter care, cat cold weather, kitten winter tips",
        "cover_image": "images/hero_home.jpg"
    },
    {
        "title": "Maine Coon Carrier Training for Stress‑Free Vet Visits",
        "excerpt": "Make the carrier a safe space with a few simple training steps.",
        "content": (
            "Leave the carrier out with soft bedding so your kitten can explore it freely. "
            "Use treats to create positive associations.\n\n"
            "Practice short, calm trips before vet visits. "
            "Keep the carrier stable and quiet during travel.\n\n"
            "Carrier training reduces stress and keeps vet days calm."
        ),
        "meta_title": "Maine Coon Carrier Training | Frostline Coons",
        "meta_description": "Tips for carrier training a Maine Coon kitten to reduce stress during vet visits.",
        "keywords": "cat carrier training, Maine Coon vet visit, kitten travel",
        "cover_image": "images/hero_delivery.jpg"
    }
]


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def add_missing_columns(conn, table, columns):
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def init_db():
    conn = get_db()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS kittens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            gender TEXT,
            personality TEXT,
            price REAL DEFAULT 0,
            weight TEXT,
            registration TEXT,
            sire_name TEXT,
            sire_weight TEXT,
            sire_color TEXT,
            sire_image TEXT,
            sire_about TEXT,
            dam_name TEXT,
            dam_weight TEXT,
            dam_color TEXT,
            dam_image TEXT,
            dam_about TEXT,
            video_url TEXT,
            folder TEXT,
            image_count INTEGER DEFAULT 0,
            featured INTEGER DEFAULT 0,
            health_details TEXT,
            color TEXT,
            coat TEXT,
            energy TEXT,
            good_with TEXT,
            bio TEXT,
            highlights TEXT,
            availability TEXT DEFAULT 'Available',
            description TEXT,
            images TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    add_missing_columns(
        conn,
        "kittens",
        {
            "age": "INTEGER",
            "gender": "TEXT",
            "personality": "TEXT",
            "price": "REAL DEFAULT 0",
            "weight": "TEXT",
            "registration": "TEXT",
            "sire_name": "TEXT",
            "sire_weight": "TEXT",
            "sire_color": "TEXT",
            "sire_image": "TEXT",
            "sire_about": "TEXT",
            "dam_name": "TEXT",
            "dam_weight": "TEXT",
            "dam_color": "TEXT",
            "dam_image": "TEXT",
            "dam_about": "TEXT",
            "video_url": "TEXT",
            "folder": "TEXT",
            "image_count": "INTEGER DEFAULT 0",
            "featured": "INTEGER DEFAULT 0",
            "health_details": "TEXT",
            "color": "TEXT",
            "coat": "TEXT",
            "energy": "TEXT",
            "good_with": "TEXT",
            "bio": "TEXT",
            "highlights": "TEXT",
            "availability": "TEXT DEFAULT 'Available'",
            "description": "TEXT",
            "images": "TEXT"
        },
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS testimonials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT,
            quote TEXT,
            image TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS site_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_key TEXT UNIQUE,
            title TEXT,
            body TEXT,
            image TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            title TEXT,
            meta_title TEXT,
            meta_description TEXT,
            hero_title TEXT,
            hero_body TEXT,
            hero_image TEXT,
            steps_json TEXT,
            blocks_json TEXT,
            cta_title TEXT,
            cta_body TEXT,
            cta_label TEXT,
            cta_link TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            slug TEXT UNIQUE,
            excerpt TEXT,
            content TEXT,
            cover_image TEXT,
            meta_title TEXT,
            meta_description TEXT,
            keywords TEXT,
            status TEXT DEFAULT 'published',
            published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kitten_id INTEGER,
            name TEXT,
            email TEXT,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'open',
            inquiry_type TEXT,
            phone TEXT,
            delivery_type TEXT,
            address TEXT,
            payment_method TEXT
        )
        """
    )

    add_missing_columns(
        conn,
        "inquiries",
        {
            "status": "TEXT DEFAULT 'open'",
            "inquiry_type": "TEXT",
            "phone": "TEXT",
            "delivery_type": "TEXT",
            "address": "TEXT",
            "payment_method": "TEXT",
            "deposit_amount": "REAL",
            "balance_due": "REAL",
        },
    )

    seed_defaults(conn)
    conn.commit()
    conn.close()


def seed_defaults(conn):
    kitten_rows = conn.execute("SELECT * FROM kittens").fetchall()
    existing_by_name = {row["name"]: row for row in kitten_rows}

    for kitten in DEFAULT_KITTENS:
        row = existing_by_name.get(kitten["name"])
        payload = {
            "name": kitten["name"],
            "age": kitten["age"],
            "gender": kitten["gender"],
            "personality": kitten["personality"],
            "price": kitten["price"],
            "weight": kitten.get("weight", ""),
            "registration": kitten.get("registration", ""),
            "sire_name": kitten.get("sire_name", ""),
            "sire_weight": kitten.get("sire_weight", ""),
            "sire_color": kitten.get("sire_color", ""),
            "sire_image": kitten.get("sire_image", ""),
            "dam_name": kitten.get("dam_name", ""),
            "dam_weight": kitten.get("dam_weight", ""),
            "dam_color": kitten.get("dam_color", ""),
            "dam_image": kitten.get("dam_image", ""),
            "folder": kitten["folder"],
            "image_count": kitten["image_count"],
            "featured": 1 if kitten["featured"] else 0,
            "health_details": kitten["health_details"],
            "color": kitten["color"],
            "coat": kitten["coat"],
            "energy": kitten["energy"],
            "good_with": json.dumps(kitten["good_with"]),
            "bio": kitten["bio"],
            "highlights": json.dumps(kitten["highlights"]),
            "availability": "Available"
        }

        if row:
            updates = {}
            for key, value in payload.items():
                if key not in row.keys():
                    updates[key] = value
                else:
                    current = row[key]
                    if current is None or current == "":
                        updates[key] = value
            if updates:
                set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
                conn.execute(
                    f"UPDATE kittens SET {set_clause} WHERE id=?",
                    (*updates.values(), row["id"]),
                )
        else:
            columns = ", ".join(payload.keys())
            placeholders = ", ".join(["?"] * len(payload))
            conn.execute(
                f"INSERT INTO kittens ({columns}) VALUES ({placeholders})",
                tuple(payload.values()),
            )

    testimonial_count = conn.execute("SELECT COUNT(*) FROM testimonials").fetchone()[0]
    if testimonial_count == 0:
        for item in DEFAULT_TESTIMONIALS:
            conn.execute(
                "INSERT INTO testimonials (author, quote, image) VALUES (?, ?, ?)",
                (item["author"], item["quote"], item["image"]),
            )

    existing_sections = {
        row["section_key"]: row
        for row in conn.execute("SELECT * FROM site_sections").fetchall()
    }
    for section in DEFAULT_SECTIONS:
        row = existing_sections.get(section["key"])
        if row:
            updates = {}
            if not row["title"]:
                updates["title"] = section["title"]
            if not row["body"]:
                updates["body"] = section["body"]
            if not row["image"]:
                updates["image"] = section["image"]
            if updates:
                set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
                conn.execute(
                    f"UPDATE site_sections SET {set_clause} WHERE section_key=?",
                    (*updates.values(), section["key"]),
                )
        else:
            conn.execute(
                """
                INSERT INTO site_sections (section_key, title, body, image)
                VALUES (?, ?, ?, ?)
                """,
                (section["key"], section["title"], section["body"], section["image"]),
            )

    existing_pages = {
        row["slug"]: row for row in conn.execute("SELECT * FROM pages").fetchall()
    }
    for page in DEFAULT_PAGES:
        row = existing_pages.get(page["slug"])
        payload = {
            "title": page["title"],
            "meta_title": page["meta_title"],
            "meta_description": page["meta_description"],
            "hero_title": page["hero_title"],
            "hero_body": page["hero_body"],
            "hero_image": page["hero_image"],
            "steps_json": json.dumps(page["steps"]),
            "blocks_json": json.dumps(page["blocks"]),
            "cta_title": page["cta_title"],
            "cta_body": page["cta_body"],
            "cta_label": page["cta_label"],
            "cta_link": page["cta_link"],
        }
        if row:
            updates = {}
            for key, value in payload.items():
                if not row[key]:
                    updates[key] = value
            if updates:
                set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
                conn.execute(
                    f"UPDATE pages SET {set_clause} WHERE slug=?",
                    (*updates.values(), page["slug"]),
                )
        else:
            columns = ", ".join(["slug"] + list(payload.keys()))
            placeholders = ", ".join(["?"] * (len(payload) + 1))
            conn.execute(
                f"INSERT INTO pages ({columns}) VALUES ({placeholders})",
                (page["slug"], *payload.values()),
            )

    blog_count = conn.execute("SELECT COUNT(*) FROM blog_posts").fetchone()[0]
    if blog_count == 0:
        for post in DEFAULT_BLOG_POSTS:
            slug = ensure_unique_slug(conn, slugify(post["title"]))
            conn.execute(
                """
                INSERT INTO blog_posts
                (title, slug, excerpt, content, cover_image, meta_title, meta_description, keywords, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'published')
                """,
                (
                    post["title"],
                    slug,
                    post["excerpt"],
                    post["content"],
                    post["cover_image"],
                    post["meta_title"],
                    post["meta_description"],
                    post["keywords"],
                ),
            )


def decode_list(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return [item.strip() for item in value.split(",") if item.strip()]


def parse_list_text(value):
    if not value:
        return []
    if "\n" in value:
        return [line.strip() for line in value.splitlines() if line.strip()]
    return [item.strip() for item in value.split(",") if item.strip()]


def is_external_url(value):
    return value.startswith("http://") or value.startswith("https://")


def media_url(path):
    if not path:
        return ""
    if is_external_url(path):
        return path
    if path.startswith("/uploads/"):
        return path
    if path.startswith("/static/"):
        return path
    if path.startswith("uploads/"):
        return url_for("uploaded_file", filename=path[len("uploads/"):])
    return url_for("static", filename=path)


def kitten_folder_paths(folder):
    upload_root = os.path.join(app.config["UPLOADS_PATH"], "kittens")
    upload_path = os.path.join(upload_root, folder)
    static_path = os.path.join(app.root_path, "static", "images", folder)
    if os.path.isdir(upload_path):
        return upload_path, True
    if os.path.isdir(static_path):
        return static_path, False
    return upload_path, True


def kitten_image_url(folder, filename):
    if not folder:
        return url_for("static", filename="images/hero_kitten.jpg")
    folder_path, uses_uploads = kitten_folder_paths(folder)
    if uses_uploads:
        return url_for(
            "uploaded_file", filename=f"kittens/{folder}/{filename}"
        )
    return url_for("static", filename=f"images/{folder}/{filename}")


@app.context_processor
def inject_media_helpers():
    sections = fetch_sections()
    return {
        "media_url": media_url,
        "kitten_image_url": kitten_image_url,
        "site_sections": sections,
    }


def kitten_row_to_dict(row):
    kitten = dict(row)
    kitten["age"] = int(kitten.get("age") or 0)
    kitten["price"] = float(kitten.get("price") or 0)
    kitten["weight"] = kitten.get("weight") or ""
    kitten["registration"] = kitten.get("registration") or ""
    kitten["sire_name"] = kitten.get("sire_name") or ""
    kitten["sire_weight"] = kitten.get("sire_weight") or ""
    kitten["sire_color"] = kitten.get("sire_color") or ""
    kitten["sire_image"] = kitten.get("sire_image") or ""
    kitten["sire_about"] = kitten.get("sire_about") or ""
    kitten["dam_name"] = kitten.get("dam_name") or ""
    kitten["dam_weight"] = kitten.get("dam_weight") or ""
    kitten["dam_color"] = kitten.get("dam_color") or ""
    kitten["dam_image"] = kitten.get("dam_image") or ""
    kitten["dam_about"] = kitten.get("dam_about") or ""
    kitten["video_url"] = kitten.get("video_url") or ""
    kitten["image_count"] = int(kitten.get("image_count") or 0)
    kitten["featured"] = bool(kitten.get("featured"))
    availability = kitten.get("availability") or "Available"
    kitten["availability"] = availability.title()
    kitten["good_with"] = decode_list(kitten.get("good_with"))
    kitten["highlights"] = decode_list(kitten.get("highlights"))
    kitten["bio"] = kitten.get("bio") or kitten.get("description") or ""
    kitten["health_details"] = kitten.get("health_details") or ""
    kitten["personality"] = kitten.get("personality") or ""
    kitten["coat"] = kitten.get("coat") or ""
    kitten["energy"] = kitten.get("energy") or ""
    kitten["color"] = kitten.get("color") or ""
    kitten["folder"] = kitten.get("folder") or ""

    local_images = list_kitten_images(kitten["folder"])
    extra_images = [item.strip() for item in decode_list(kitten.get("images")) if item.strip()]
    kitten["image_urls"] = extra_images

    if local_images:
        kitten["images"] = local_images
        kitten["image_count"] = len(local_images)
        kitten["main_image"] = "1.jpg" if "1.jpg" in local_images else local_images[0]
    else:
        kitten["images"] = []
        kitten["main_image"] = "1.jpg"

    default_image = url_for("static", filename="images/hero_kitten.jpg")
    if local_images:
        main_image_url = kitten_image_url(kitten["folder"], kitten["main_image"])
    elif extra_images:
        main_image_url = media_url(extra_images[0])
    else:
        main_image_url = default_image

    gallery = [
        {"type": "image", "src": kitten_image_url(kitten["folder"], img)}
        for img in local_images
    ]
    gallery += [{"type": "image", "src": media_url(img)} for img in extra_images]

    video_src = media_url(kitten["video_url"]) if kitten["video_url"] else ""
    if video_src:
        gallery.append({"type": "video", "src": video_src})

    main_media_type = "image"
    main_media_src = main_image_url
    if not local_images and not extra_images and video_src:
        main_media_type = "video"
        main_media_src = video_src

    kitten["gallery"] = gallery
    kitten["main_media_type"] = main_media_type
    kitten["main_media_src"] = main_media_src
    kitten["card_image_url"] = main_image_url if main_image_url else default_image
    kitten["video_src"] = video_src
    return kitten


def fetch_kittens(featured_only=False):
    conn = get_db()
    query = "SELECT * FROM kittens"
    params = ()
    if featured_only:
        query += " WHERE featured = 1"
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [kitten_row_to_dict(row) for row in rows]


def fetch_kitten(kitten_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM kittens WHERE id = ?", (kitten_id,)).fetchone()
    conn.close()
    return kitten_row_to_dict(row) if row else None


def fetch_testimonials():
    conn = get_db()
    rows = conn.execute("SELECT * FROM testimonials ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_sections():
    conn = get_db()
    rows = conn.execute("SELECT * FROM site_sections").fetchall()
    conn.close()
    return {row["section_key"]: dict(row) for row in rows}


def safe_json_load(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def fetch_page(slug):
    conn = get_db()
    row = conn.execute("SELECT * FROM pages WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    if not row:
        return None
    page = dict(row)
    default = next((item for item in DEFAULT_PAGES if item["slug"] == slug), None)
    page["steps"] = safe_json_load(page.get("steps_json"), default["steps"] if default else [])
    page["blocks"] = safe_json_load(page.get("blocks_json"), default["blocks"] if default else [])
    return page


def fetch_blog_posts(published_only=True):
    conn = get_db()
    if published_only:
        rows = conn.execute(
            "SELECT * FROM blog_posts WHERE status = 'published' ORDER BY published_at DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM blog_posts ORDER BY published_at DESC"
        ).fetchall()
    conn.close()
    posts = []
    for row in rows:
        post = dict(row)
        if not post.get("excerpt") and post.get("content"):
            post["excerpt"] = post["content"][:160].rsplit(" ", 1)[0] + "..."
        posts.append(post)
    return posts


def fetch_blog_post_by_slug(slug):
    conn = get_db()
    row = conn.execute("SELECT * FROM blog_posts WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    if not row:
        return None
    post = dict(row)
    if not post.get("excerpt") and post.get("content"):
        post["excerpt"] = post["content"][:160].rsplit(" ", 1)[0] + "..."
    return post


def ensure_unique_slug(conn, base_slug, post_id=None):
    slug = base_slug
    counter = 1
    while True:
        params = (slug,)
        query = "SELECT id FROM blog_posts WHERE slug = ?"
        row = conn.execute(query, params).fetchone()
        if not row or (post_id and row["id"] == post_id):
            return slug
        counter += 1
        slug = f"{base_slug}-{counter}"


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def save_uploaded_files(files, folder_path, allowed_exts):
    saved_files = []
    os.makedirs(folder_path, exist_ok=True)
    for index, file in enumerate(files, start=1):
        filename = secure_filename(file.filename)
        if not filename:
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_exts:
            raise ValueError("Unsupported file type. Please upload JPG images.")
        if ext in {".jpg", ".jpeg"}:
            destination = os.path.join(folder_path, f"{index}.jpg")
        else:
            destination = os.path.join(folder_path, f"{index}{ext}")
        file.save(destination)
        saved_files.append(destination)
    return saved_files


def slugify(value):
    safe = []
    for char in value.lower():
        if char.isalnum():
            safe.append(char)
        else:
            if not safe or safe[-1] != "-":
                safe.append("-")
    return "".join(safe).strip("-")


def list_kitten_images(folder):
    if not folder:
        return []
    folder_path, _ = kitten_folder_paths(folder)
    if not os.path.isdir(folder_path):
        return []
    files = [
        f
        for f in os.listdir(folder_path)
        if os.path.splitext(f)[1].lower() in ALLOWED_KITTEN_IMAGE_EXTS
    ]

    def sort_key(name):
        stem = os.path.splitext(name)[0]
        if stem.isdigit():
            return (0, int(stem))
        return (1, name.lower())

    return sorted(files, key=sort_key)


def set_main_image(folder, filename):
    if not folder or not filename:
        return
    folder_path, _ = kitten_folder_paths(folder)
    target = os.path.join(folder_path, filename)
    main = os.path.join(folder_path, "1.jpg")
    if not os.path.exists(target):
        return
    if os.path.abspath(target) == os.path.abspath(main):
        return

    temp = os.path.join(folder_path, "__temp_main.jpg")
    if os.path.exists(main):
        os.replace(main, temp)
        os.replace(target, main)
        os.replace(temp, target)
    else:
        os.replace(target, main)


def save_kitten(kitten_id=None):
    name = request.form.get("name", "").strip()
    if not name:
        flash("Name is required.", "error")
        return redirect(request.url)

    existing = fetch_kitten(kitten_id) if kitten_id else None

    folder = request.form.get("folder", "").strip() or (existing["folder"] if existing else "")
    folder = secure_filename(folder) if folder else ""
    if not folder:
        folder = slugify(name) or "kitten"

    sire_image = request.form.get("sire_image", "").strip() or (existing.get("sire_image") if existing else "")
    dam_image = request.form.get("dam_image", "").strip() or (existing.get("dam_image") if existing else "")

    video_url = request.form.get("video_url", "").strip() or (existing.get("video_url") if existing else "")
    remove_video = request.form.get("remove_video") == "on"

    image_urls = [item.strip() for item in parse_list_text(request.form.get("image_urls", "")) if item.strip()]

    for parent_key in ("sire", "dam"):
        upload = request.files.get(f"{parent_key}_image_upload")
        if upload and upload.filename:
            ext = os.path.splitext(upload.filename)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                flash("Unsupported parent image type.", "error")
                return redirect(request.url)
            folder_path = os.path.join(app.config["UPLOADS_PATH"], "parents")
            os.makedirs(folder_path, exist_ok=True)
            filename = f"{slugify(name)}-{parent_key}{ext}"
            upload.save(os.path.join(folder_path, filename))
            if parent_key == "sire":
                sire_image = f"uploads/parents/{filename}"
            else:
                dam_image = f"uploads/parents/{filename}"

    images = [f for f in request.files.getlist("images") if f and f.filename]
    image_count = int(request.form.get("image_count") or (existing["image_count"] if existing else 0))

    if images:
        try:
            folder_path = os.path.join(app.config["UPLOADS_PATH"], "kittens", folder)
            saved = save_uploaded_files(images, folder_path, ALLOWED_KITTEN_IMAGE_EXTS)
            image_count = len(saved)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(request.url)
    elif kitten_id is None and image_count == 0 and not image_urls:
        flash("Please upload at least one JPG image or add an image URL.", "error")
        return redirect(request.url)

    image_files = list_kitten_images(folder)
    if image_files:
        image_count = len(image_files)

    video_upload = request.files.get("video_upload")
    if video_upload and video_upload.filename:
        ext = os.path.splitext(video_upload.filename)[1].lower()
        if ext not in ALLOWED_VIDEO_EXTS:
            flash("Unsupported video type. Please upload MP4, WebM, or MOV.", "error")
            return redirect(request.url)
        folder_path = os.path.join(app.config["UPLOADS_PATH"], "videos")
        os.makedirs(folder_path, exist_ok=True)
        filename = f"{slugify(name) or 'kitten'}-video{ext}"
        video_upload.save(os.path.join(folder_path, filename))
        video_url = f"uploads/videos/{filename}"

    if remove_video and not (video_upload and video_upload.filename):
        video_url = ""

    availability = request.form.get("availability", "").strip().title()
    if availability not in {"Available", "Reserved", "Sold"}:
        availability = "Available"

    payload = {
        "name": name,
        "age": int(request.form.get("age") or 0),
        "gender": request.form.get("gender", "").strip(),
        "personality": request.form.get("personality", "").strip(),
        "price": float(request.form.get("price") or 0),
        "weight": request.form.get("weight", "").strip(),
        "registration": request.form.get("registration", "").strip(),
        "sire_name": request.form.get("sire_name", "").strip(),
        "sire_weight": request.form.get("sire_weight", "").strip(),
        "sire_color": request.form.get("sire_color", "").strip(),
        "sire_image": sire_image,
        "sire_about": request.form.get("sire_about", "").strip(),
        "dam_name": request.form.get("dam_name", "").strip(),
        "dam_weight": request.form.get("dam_weight", "").strip(),
        "dam_color": request.form.get("dam_color", "").strip(),
        "dam_image": dam_image,
        "dam_about": request.form.get("dam_about", "").strip(),
        "video_url": video_url,
        "folder": folder,
        "image_count": image_count,
        "featured": 1 if request.form.get("featured") == "on" else 0,
        "health_details": request.form.get("health_details", "").strip(),
        "color": request.form.get("color", "").strip(),
        "coat": request.form.get("coat", "").strip(),
        "energy": request.form.get("energy", "").strip(),
        "good_with": json.dumps(parse_list_text(request.form.get("good_with", ""))),
        "bio": request.form.get("bio", "").strip(),
        "highlights": json.dumps(parse_list_text(request.form.get("highlights", ""))),
        "availability": availability,
        "images": json.dumps(image_urls)
    }

    conn = get_db()
    if kitten_id:
        set_clause = ", ".join([f"{k}=?" for k in payload.keys()])
        conn.execute(
            f"UPDATE kittens SET {set_clause} WHERE id = ?",
            (*payload.values(), kitten_id),
        )
        conn.commit()
        conn.close()
        flash("Kitten updated.", "success")
    else:
        columns = ", ".join(payload.keys())
        placeholders = ", ".join(["?"] * len(payload))
        conn.execute(
            f"INSERT INTO kittens ({columns}) VALUES ({placeholders})",
            tuple(payload.values()),
        )
        conn.commit()
        conn.close()
        flash("Kitten added.", "success")

    return redirect(url_for("admin_kittens"))


def save_testimonial(testimonial_id=None):
    author = request.form.get("author", "").strip()
    quote = request.form.get("quote", "").strip()
    if not author or not quote:
        flash("Author and quote are required.", "error")
        return redirect(request.url)

    image_path = request.form.get("image", "").strip()
    upload = request.files.get("image_upload")
    if upload and upload.filename:
        ext = os.path.splitext(upload.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTS:
            flash("Unsupported image type.", "error")
            return redirect(request.url)
        folder = os.path.join(app.config["UPLOADS_PATH"], "testimonials")
        os.makedirs(folder, exist_ok=True)
        filename = f"{slugify(author) or 'testimonial'}{ext}"
        upload.save(os.path.join(folder, filename))
        image_path = f"uploads/testimonials/{filename}"

    conn = get_db()
    if testimonial_id:
        conn.execute(
            """
            UPDATE testimonials
            SET author = ?, quote = ?, image = ?
            WHERE id = ?
            """,
            (author, quote, image_path, testimonial_id),
        )
        conn.commit()
        conn.close()
        flash("Testimonial updated.", "success")
    else:
        conn.execute(
            "INSERT INTO testimonials (author, quote, image) VALUES (?, ?, ?)",
            (author, quote, image_path),
        )
        conn.commit()
        conn.close()
        flash("Testimonial added.", "success")

    return redirect(url_for("admin_testimonials"))


def save_blog_post(post_id=None):
    title = request.form.get("title", "").strip()
    if not title:
        flash("Title is required.", "error")
        return redirect(request.url)

    slug_input = request.form.get("slug", "").strip()
    base_slug = slugify(slug_input or title)

    excerpt = request.form.get("excerpt", "").strip()
    content = request.form.get("content", "").strip()
    meta_title = request.form.get("meta_title", "").strip()
    meta_description = request.form.get("meta_description", "").strip()
    keywords = request.form.get("keywords", "").strip()
    status = request.form.get("status", "published").strip() or "published"
    published_at = request.form.get("published_at", "").strip()

    cover_image = request.form.get("cover_image", "").strip()
    upload = request.files.get("cover_upload")
    if upload and upload.filename:
        ext = os.path.splitext(upload.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTS:
            flash("Unsupported image type.", "error")
            return redirect(request.url)
        folder = os.path.join(app.config["UPLOADS_PATH"], "blog")
        os.makedirs(folder, exist_ok=True)
        filename = f"{base_slug}{ext}"
        upload.save(os.path.join(folder, filename))
        cover_image = f"uploads/blog/{filename}"

    conn = get_db()
    slug = ensure_unique_slug(conn, base_slug, post_id)

    if post_id:
        conn.execute(
            """
            UPDATE blog_posts
            SET title = ?, slug = ?, excerpt = ?, content = ?, cover_image = ?,
                meta_title = ?, meta_description = ?, keywords = ?, status = ?,
                published_at = COALESCE(NULLIF(?, ''), published_at),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                title,
                slug,
                excerpt,
                content,
                cover_image,
                meta_title,
                meta_description,
                keywords,
                status,
                published_at,
                post_id,
            ),
        )
        conn.commit()
        conn.close()
        flash("Blog post updated.", "success")
    else:
        conn.execute(
            """
            INSERT INTO blog_posts
            (title, slug, excerpt, content, cover_image, meta_title, meta_description, keywords, status, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(NULLIF(?, ''), CURRENT_TIMESTAMP))
            """,
            (
                title,
                slug,
                excerpt,
                content,
                cover_image,
                meta_title,
                meta_description,
                keywords,
                status,
                published_at,
            ),
        )
        conn.commit()
        conn.close()
        flash("Blog post created.", "success")

    return redirect(url_for("admin_blog"))


def save_delivery_page():
    title = request.form.get("title", "").strip()
    meta_title = request.form.get("meta_title", "").strip()
    meta_description = request.form.get("meta_description", "").strip()
    hero_title = request.form.get("hero_title", "").strip()
    hero_body = request.form.get("hero_body", "").strip()
    hero_image = request.form.get("hero_image", "").strip()

    hero_upload = request.files.get("hero_image_upload")
    if hero_upload and hero_upload.filename:
        ext = os.path.splitext(hero_upload.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTS:
            flash("Unsupported hero image type.", "error")
            return redirect(request.url)
        folder = os.path.join(app.config["UPLOADS_PATH"], "pages")
        os.makedirs(folder, exist_ok=True)
        filename = f"delivery-hero{ext}"
        hero_upload.save(os.path.join(folder, filename))
        hero_image = f"uploads/pages/{filename}"

    steps = []
    for idx in range(1, 4):
        step_title = request.form.get(f"step_title_{idx}", "").strip()
        step_body = request.form.get(f"step_body_{idx}", "").strip()
        if step_title or step_body:
            steps.append({"title": step_title, "body": step_body})

    blocks = []
    for idx in range(1, 5):
        block_title = request.form.get(f"block_title_{idx}", "").strip()
        block_body = request.form.get(f"block_body_{idx}", "").strip()
        block_image = request.form.get(f"block_image_{idx}", "").strip()
        layout = request.form.get(f"block_layout_{idx}", "left").strip() or "left"

        upload = request.files.get(f"block_image_upload_{idx}")
        if upload and upload.filename:
            ext = os.path.splitext(upload.filename)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                flash("Unsupported block image type.", "error")
                return redirect(request.url)
            folder = os.path.join(app.config["UPLOADS_PATH"], "pages")
            os.makedirs(folder, exist_ok=True)
            filename = f"delivery-block-{idx}{ext}"
            upload.save(os.path.join(folder, filename))
            block_image = f"uploads/pages/{filename}"

        if block_title or block_body or block_image:
            blocks.append(
                {
                    "title": block_title,
                    "body": block_body,
                    "image": block_image,
                    "layout": layout,
                }
            )

    cta_title = request.form.get("cta_title", "").strip()
    cta_body = request.form.get("cta_body", "").strip()
    cta_label = request.form.get("cta_label", "").strip()
    cta_link = request.form.get("cta_link", "").strip()

    conn = get_db()
    conn.execute(
        """
        UPDATE pages
        SET title = ?, meta_title = ?, meta_description = ?, hero_title = ?, hero_body = ?, hero_image = ?,
            steps_json = ?, blocks_json = ?, cta_title = ?, cta_body = ?, cta_label = ?, cta_link = ?
        WHERE slug = 'delivery'
        """,
        (
            title,
            meta_title,
            meta_description,
            hero_title,
            hero_body,
            hero_image,
            json.dumps(steps),
            json.dumps(blocks),
            cta_title,
            cta_body,
            cta_label,
            cta_link,
        ),
    )
    conn.commit()
    conn.close()
    flash("Delivery page updated.", "success")
    return redirect(url_for("admin_delivery_page"))


def save_generic_page(slug):
    title = request.form.get("title", "").strip()
    meta_title = request.form.get("meta_title", "").strip()
    meta_description = request.form.get("meta_description", "").strip()
    hero_title = request.form.get("hero_title", "").strip()
    hero_body = request.form.get("hero_body", "").strip()
    hero_image = request.form.get("hero_image", "").strip()

    hero_upload = request.files.get("hero_image_upload")
    if hero_upload and hero_upload.filename:
        ext = os.path.splitext(hero_upload.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTS:
            flash("Unsupported hero image type.", "error")
            return redirect(request.url)
        folder = os.path.join(app.config["UPLOADS_PATH"], "pages")
        os.makedirs(folder, exist_ok=True)
        filename = f"{slug}-hero{ext}"
        hero_upload.save(os.path.join(folder, filename))
        hero_image = f"uploads/pages/{filename}"

    blocks = []
    for idx in range(1, 5):
        block_title = request.form.get(f"block_title_{idx}", "").strip()
        block_body = request.form.get(f"block_body_{idx}", "").strip()
        block_image = request.form.get(f"block_image_{idx}", "").strip()
        layout = request.form.get(f"block_layout_{idx}", "left").strip() or "left"

        upload = request.files.get(f"block_image_upload_{idx}")
        if upload and upload.filename:
            ext = os.path.splitext(upload.filename)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                flash("Unsupported block image type.", "error")
                return redirect(request.url)
            folder = os.path.join(app.config["UPLOADS_PATH"], "pages")
            os.makedirs(folder, exist_ok=True)
            filename = f"{slug}-block-{idx}{ext}"
            upload.save(os.path.join(folder, filename))
            block_image = f"uploads/pages/{filename}"

        if block_title or block_body or block_image:
            blocks.append(
                {
                    "title": block_title,
                    "body": block_body,
                    "image": block_image,
                    "layout": layout,
                }
            )

    cta_title = request.form.get("cta_title", "").strip()
    cta_body = request.form.get("cta_body", "").strip()
    cta_label = request.form.get("cta_label", "").strip()
    cta_link = request.form.get("cta_link", "").strip()

    conn = get_db()
    conn.execute(
        """
        UPDATE pages
        SET title = ?, meta_title = ?, meta_description = ?, hero_title = ?, hero_body = ?, hero_image = ?,
            blocks_json = ?, cta_title = ?, cta_body = ?, cta_label = ?, cta_link = ?
        WHERE slug = ?
        """,
        (
            title,
            meta_title,
            meta_description,
            hero_title,
            hero_body,
            hero_image,
            json.dumps(blocks),
            cta_title,
            cta_body,
            cta_label,
            cta_link,
            slug,
        ),
    )
    conn.commit()
    conn.close()
    flash("Page updated.", "success")
    return redirect(url_for("admin_pages"))


def send_inquiry_email(inquiry, kitten):
    if not app.config["SMTP_HOST"]:
        return

    subject = f"New {inquiry['inquiry_type'].title()} Inquiry - {kitten.get('name', 'Kitten')}"
    to_addr = app.config["SMTP_TO"]
    from_addr = app.config["SMTP_FROM"]

    total = f"${kitten.get('price', 0):.0f}"
    deposit = f"${inquiry.get('deposit_amount', 0):.0f}"
    balance = f"${inquiry.get('balance_due', 0):.0f}"
    invoice_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f6f2ec; padding:24px;">
      <div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:16px;padding:24px;">
        <h2 style="margin-top:0;color:#2c2a28;">Frostline Coons — Inquiry Invoice</h2>
        <p style="color:#4a453f;">New {inquiry['inquiry_type']} inquiry received.</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
          <tr>
            <th align="left" style="padding:8px;border-bottom:1px solid #eee;">Item</th>
            <th align="right" style="padding:8px;border-bottom:1px solid #eee;">Price</th>
          </tr>
          <tr>
            <td style="padding:8px;">{kitten.get('name', 'Kitten')} ({kitten.get('gender', '')})</td>
            <td align="right" style="padding:8px;">{total}</td>
          </tr>
          <tr>
            <td style="padding:8px;">Reservation Amount</td>
            <td align="right" style="padding:8px;">{deposit}</td>
          </tr>
          <tr>
            <td style="padding:8px;">Balance Due</td>
            <td align="right" style="padding:8px;">{balance}</td>
          </tr>
          <tr>
            <td style="padding:8px;font-weight:bold;">Total</td>
            <td align="right" style="padding:8px;font-weight:bold;">{total}</td>
          </tr>
        </table>
        <h3 style="margin-bottom:6px;">Customer Details</h3>
        <p style="margin:0;">Name: {inquiry['name']}</p>
        <p style="margin:0;">Email: {inquiry['email']}</p>
        <p style="margin:0;">Phone: {inquiry.get('phone') or '—'}</p>
        <p style="margin:0;">Delivery: {inquiry.get('delivery_type') or '—'}</p>
        <p style="margin:0;">Address: {inquiry.get('address') or '—'}</p>
        <p style="margin:0;">Payment: {inquiry.get('payment_method') or '—'}</p>
        <p style="margin-top:16px;color:#4a453f;">Message:</p>
        <p style="margin:0;color:#2c2a28;">{inquiry['message'] or '—'}</p>
      </div>
    </body>
    </html>
    """

    invoice_text = (
        f"New {inquiry['inquiry_type']} inquiry\n"
        f"Kitten: {kitten.get('name', 'Kitten')} - {total}\n"
        f"Reservation Amount: {deposit}\n"
        f"Balance Due: {balance}\n"
        f"Name: {inquiry['name']}\n"
        f"Email: {inquiry['email']}\n"
        f"Phone: {inquiry.get('phone') or '-'}\n"
        f"Delivery: {inquiry.get('delivery_type') or '-'}\n"
        f"Address: {inquiry.get('address') or '-'}\n"
        f"Payment: {inquiry.get('payment_method') or '-'}\n"
        f"Message: {inquiry['message'] or '-'}\n"
    )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_addr
    message["To"] = to_addr
    message.set_content(invoice_text)
    message.add_alternative(invoice_html, subtype="html")

    if app.config["SMTP_USE_SSL"]:
        with smtplib.SMTP_SSL(app.config["SMTP_HOST"], app.config["SMTP_PORT"]) as server:
            if app.config["SMTP_USER"]:
                server.login(app.config["SMTP_USER"], app.config["SMTP_PASS"])
            server.send_message(message)
    else:
        with smtplib.SMTP(app.config["SMTP_HOST"], app.config["SMTP_PORT"]) as server:
            if app.config["SMTP_USE_TLS"]:
                server.starttls()
            if app.config["SMTP_USER"]:
                server.login(app.config["SMTP_USER"], app.config["SMTP_PASS"])
            server.send_message(message)


init_db()

# -------------------- ROUTES --------------------
@app.route("/")
def index():
    featured = fetch_kittens(featured_only=True)
    testimonials = fetch_testimonials()
    sections = fetch_sections()
    hero = sections.get("hero") if sections else None
    hero_image = hero.get("image") if hero and hero.get("image") else "images/hero_kitten.jpg"
    return render_template(
        "index.html",
        featured=featured,
        testimonials=testimonials,
        sections=sections,
        meta_title="Frostline Coons | Maine Coon Kittens",
        meta_description=(
            "Ethically raised Maine Coon kittens with loving socialization, "
            "health-focused care, and lifelong support."
        ),
        meta_image=media_url(hero_image),
    )


@app.route("/available_kittens")
def available_kittens():
    kittens = fetch_kittens()[:12]
    meta_image = kittens[0].get("card_image_url") if kittens else media_url("images/hero_kitten.jpg")
    return render_template(
        "available_kittens.html",
        kittens=kittens,
        meta_title="Available Maine Coon Kittens | Frostline Coons",
        meta_description="View available Maine Coon kittens, pricing, and details. Reserve or inquire today.",
        meta_image=meta_image,
    )


@app.route("/kitten/<int:kitten_id>")
def kitten_details(kitten_id):
    kitten = fetch_kitten(kitten_id)
    if not kitten:
        abort(404)
    sections = fetch_sections()
    meta_image = kitten.get("card_image_url") or media_url("images/hero_kitten.jpg")
    return render_template(
        "kitten_details.html",
        kitten=kitten,
        sections=sections,
        reservation_deposit=app.config["RESERVATION_DEPOSIT"],
        meta_title=f"{kitten.get('name', 'Kitten')} | Frostline Coons",
        meta_description=kitten.get("description")
        or kitten.get("bio")
        or "Meet this Maine Coon kitten and learn about personality, care, and availability.",
        meta_image=meta_image,
    )


@app.route("/inquiry", methods=["POST"])
def submit_inquiry():
    kitten_id = request.form.get("kitten_id")
    inquiry_type = request.form.get("inquiry_type", "reserve").strip().lower()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    message = request.form.get("message", "").strip()
    delivery_type = request.form.get("delivery_type", "").strip()
    address = request.form.get("address", "").strip()
    payment_method = request.form.get("payment_method", "").strip()

    if not kitten_id or not name or not email:
        return {"ok": False, "error": "Missing required fields."}, 400

    kitten = fetch_kitten(int(kitten_id))
    if not kitten:
        return {"ok": False, "error": "Kitten not found."}, 404
    if (kitten.get("availability") or "").lower() != "available":
        return {"ok": False, "error": "This kitten is no longer available."}, 400

    price = float(kitten.get("price") or 0)
    if inquiry_type == "reserve":
        deposit_amount = min(price, app.config["RESERVATION_DEPOSIT"])
        balance_due = max(0, price - deposit_amount)
    else:
        deposit_amount = 0
        balance_due = price

    conn = get_db()
    conn.execute(
        """
        INSERT INTO inquiries
        (kitten_id, name, email, message, status, inquiry_type, phone, delivery_type, address, payment_method, deposit_amount, balance_due)
        VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            kitten_id,
            name,
            email,
            message,
            inquiry_type,
            phone,
            delivery_type,
            address,
            payment_method,
            deposit_amount,
            balance_due,
        ),
    )
    conn.commit()
    conn.close()

    try:
        send_inquiry_email(
            {
                "name": name,
                "email": email,
                "phone": phone,
                "message": message,
                "inquiry_type": inquiry_type,
                "delivery_type": delivery_type,
                "address": address,
                "payment_method": payment_method,
                "deposit_amount": deposit_amount,
                "balance_due": balance_due,
            },
            kitten,
        )
    except Exception as exc:
        return {"ok": False, "error": f"Email failed: {exc}"}, 500

    return {"ok": True}


@app.route("/delivery")
def delivery():
    page = fetch_page("delivery")
    if not page:
        abort(404)
    return render_template(
        "delivery.html",
        page=page,
        meta_title=page.get("meta_title") or page.get("title") or "Delivery & Arrival",
        meta_description=page.get("meta_description") or page.get("hero_body"),
        meta_image=media_url(page.get("hero_image") or "images/hero_delivery.jpg"),
    )


def render_generic_page(slug):
    page = fetch_page(slug)
    if not page:
        abort(404)
    return render_template(
        "page.html",
        page=page,
        meta_title=page.get("meta_title") or page.get("title"),
        meta_description=page.get("meta_description") or page.get("hero_body"),
        meta_image=media_url(page.get("hero_image") or "images/hero_kitten.jpg"),
    )


@app.route("/about")
def about():
    return render_generic_page("about")


@app.route("/faqs")
def faqs():
    return render_generic_page("faqs")


@app.route("/contact")
def contact():
    return render_generic_page("contact")


@app.route("/blog")
def blog_index():
    posts = fetch_blog_posts()
    return render_template(
        "blog/index.html",
        posts=posts,
        meta_title="Maine Coon Blog | Frostline Coons",
        meta_description="Maine Coon care guides, breed insights, and kitten tips from Frostline Coons.",
        meta_image=media_url("images/hero_kitten.jpg"),
    )


@app.route("/blog/<slug>")
def blog_post(slug):
    post = fetch_blog_post_by_slug(slug)
    if not post or post.get("status") != "published":
        abort(404)
    cover = post.get("cover_image") or "images/hero_kitten.jpg"
    return render_template(
        "blog/post.html",
        post=post,
        meta_title=post.get("meta_title") or post.get("title") or "Maine Coon Blog",
        meta_description=post.get("meta_description") or post.get("excerpt"),
        meta_image=media_url(cover),
        og_type="article",
    )


@app.route("/sitemap.xml")
def sitemap():
    base_url = request.url_root.rstrip("/")
    urls = [
        f"{base_url}{url_for('index')}",
        f"{base_url}{url_for('available_kittens')}",
        f"{base_url}{url_for('delivery')}",
        f"{base_url}{url_for('about')}",
        f"{base_url}{url_for('faqs')}",
        f"{base_url}{url_for('contact')}",
        f"{base_url}{url_for('blog_index')}",
    ]

    for kitten in fetch_kittens():
        urls.append(f"{base_url}{url_for('kitten_details', kitten_id=kitten['id'])}")

    for post in fetch_blog_posts():
        urls.append(f"{base_url}{url_for('blog_post', slug=post['slug'])}")

    xml_items = "\n".join([f"  <url><loc>{loc}</loc></url>" for loc in urls])
    xml = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"
        f"{xml_items}\n"
        "</urlset>"
    )
    return Response(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    base_url = request.url_root.rstrip("/")
    content = "User-agent: *\nAllow: /\nSitemap: " + f"{base_url}/sitemap.xml\n"
    return Response(content, mimetype="text/plain")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOADS_PATH"], filename)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if (
            username == app.config["ADMIN_USERNAME"]
            and password == app.config["ADMIN_PASSWORD"]
        ):
            session["admin_logged_in"] = True
            return redirect(request.args.get("next") or url_for("admin_dashboard"))
        flash("Invalid credentials. Please try again.", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin_dashboard():
    conn = get_db()
    kitten_count = conn.execute("SELECT COUNT(*) FROM kittens").fetchone()[0]
    testimonial_count = conn.execute("SELECT COUNT(*) FROM testimonials").fetchone()[0]
    inquiry_count = conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]
    recent_inquiries = conn.execute(
        "SELECT * FROM inquiries ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return render_template(
        "admin/dashboard.html",
        kitten_count=kitten_count,
        testimonial_count=testimonial_count,
        inquiry_count=inquiry_count,
        recent_inquiries=recent_inquiries,
    )


@app.route("/admin/kittens")
@login_required
def admin_kittens():
    kittens = fetch_kittens()
    return render_template("admin/kittens_list.html", kittens=kittens)


@app.route("/admin/kittens/new", methods=["GET", "POST"])
@login_required
def admin_kittens_new():
    if request.method == "POST":
        return save_kitten()
    return render_template(
        "admin/kitten_form.html", kitten=None, mode="new", kitten_images=[]
    )


@app.route("/admin/kittens/<int:kitten_id>/edit", methods=["GET", "POST"])
@login_required
def admin_kittens_edit(kitten_id):
    kitten = fetch_kitten(kitten_id)
    if not kitten:
        abort(404)
    kitten_images = list_kitten_images(kitten.get("folder"))
    if request.method == "POST":
        return save_kitten(kitten_id)
    return render_template(
        "admin/kitten_form.html",
        kitten=kitten,
        mode="edit",
        kitten_images=kitten_images,
    )


@app.route("/admin/kittens/<int:kitten_id>/delete", methods=["POST"])
@login_required
def admin_kittens_delete(kitten_id):
    conn = get_db()
    conn.execute("DELETE FROM kittens WHERE id = ?", (kitten_id,))
    conn.commit()
    conn.close()
    flash("Kitten deleted.", "success")
    return redirect(url_for("admin_kittens"))


@app.route("/admin/kittens/<int:kitten_id>/images/main", methods=["POST"])
@login_required
def admin_kittens_set_main_image(kitten_id):
    kitten = fetch_kitten(kitten_id)
    if not kitten:
        abort(404)
    filename = os.path.basename(request.form.get("filename", "").strip())
    images = list_kitten_images(kitten.get("folder"))
    if filename not in images:
        flash("Image not found.", "error")
        return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))

    set_main_image(kitten.get("folder"), filename)
    flash("Main image updated.", "success")
    return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))


@app.route("/admin/kittens/<int:kitten_id>/images/delete", methods=["POST"])
@login_required
def admin_kittens_delete_image(kitten_id):
    kitten = fetch_kitten(kitten_id)
    if not kitten:
        abort(404)
    filename = os.path.basename(request.form.get("filename", "").strip())
    folder = kitten.get("folder")
    images = list_kitten_images(folder)
    if filename not in images:
        flash("Image not found.", "error")
        return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))
    if len(images) <= 1:
        flash("At least one image is required.", "error")
        return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))

    folder_path, _ = kitten_folder_paths(folder)
    path = os.path.join(folder_path, filename)
    try:
        os.remove(path)
    except FileNotFoundError:
        flash("Image not found on disk.", "error")
        return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))

    images_after = list_kitten_images(folder)
    if "1.jpg" not in images_after and images_after:
        set_main_image(folder, images_after[0])

    conn = get_db()
    conn.execute(
        "UPDATE kittens SET image_count = ? WHERE id = ?",
        (len(images_after), kitten_id),
    )
    conn.commit()
    conn.close()
    flash("Image removed.", "success")
    return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))


@app.route("/admin/testimonials")
@login_required
def admin_testimonials():
    testimonials = fetch_testimonials()
    return render_template("admin/testimonials_list.html", testimonials=testimonials)


@app.route("/admin/testimonials/new", methods=["GET", "POST"])
@login_required
def admin_testimonials_new():
    if request.method == "POST":
        return save_testimonial()
    return render_template("admin/testimonial_form.html", testimonial=None, mode="new")


@app.route("/admin/testimonials/<int:testimonial_id>/edit", methods=["GET", "POST"])
@login_required
def admin_testimonials_edit(testimonial_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM testimonials WHERE id = ?", (testimonial_id,)
    ).fetchone()
    conn.close()
    if not row:
        abort(404)
    testimonial = dict(row)
    if request.method == "POST":
        return save_testimonial(testimonial_id)
    return render_template(
        "admin/testimonial_form.html", testimonial=testimonial, mode="edit"
    )


@app.route("/admin/testimonials/<int:testimonial_id>/delete", methods=["POST"])
@login_required
def admin_testimonials_delete(testimonial_id):
    conn = get_db()
    conn.execute("DELETE FROM testimonials WHERE id = ?", (testimonial_id,))
    conn.commit()
    conn.close()
    flash("Testimonial deleted.", "success")
    return redirect(url_for("admin_testimonials"))


@app.route("/admin/sections", methods=["GET", "POST"])
@login_required
def admin_sections():
    conn = get_db()
    if request.method == "POST":
        for section in DEFAULT_SECTIONS:
            key = section["key"]
            title = request.form.get(f"{key}_title", "").strip()
            body = request.form.get(f"{key}_body", "").strip()
            image = request.form.get(f"{key}_image", "").strip()

            upload = request.files.get(f"{key}_image_upload")
            if upload and upload.filename:
                ext = os.path.splitext(upload.filename)[1].lower()
                if ext not in ALLOWED_IMAGE_EXTS:
                    flash("Unsupported image type for sections.", "error")
                    return redirect(url_for("admin_sections"))
                folder = os.path.join(app.config["UPLOADS_PATH"], "sections")
                os.makedirs(folder, exist_ok=True)
                filename = f"{key}{ext}"
                upload.save(os.path.join(folder, filename))
                image = f"uploads/sections/{filename}"

            conn.execute(
                """
                UPDATE site_sections
                SET title = ?, body = ?, image = ?
                WHERE section_key = ?
                """,
                (title, body, image, key),
            )

        conn.commit()
        conn.close()
        flash("Sections updated.", "success")
        return redirect(url_for("admin_sections"))

    rows = conn.execute("SELECT * FROM site_sections").fetchall()
    conn.close()
    sections = {row["section_key"]: dict(row) for row in rows}
    ordered = [sections[key["key"]] for key in DEFAULT_SECTIONS if key["key"] in sections]
    return render_template("admin/sections.html", sections=ordered)


@app.route("/admin/inquiries")
@login_required
def admin_inquiries():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT inquiries.*, kittens.name AS kitten_name
        FROM inquiries
        LEFT JOIN kittens ON kittens.id = inquiries.kitten_id
        ORDER BY inquiries.created_at DESC
        """
    ).fetchall()
    conn.close()
    return render_template("admin/inquiries.html", inquiries=rows)


@app.route("/admin/inquiries/<int:inquiry_id>/toggle", methods=["POST"])
@login_required
def admin_inquiries_toggle(inquiry_id):
    conn = get_db()
    row = conn.execute(
        "SELECT status FROM inquiries WHERE id = ?", (inquiry_id,)
    ).fetchone()
    if not row:
        conn.close()
        abort(404)
    new_status = "fulfilled" if row["status"] != "fulfilled" else "open"
    conn.execute(
        "UPDATE inquiries SET status = ? WHERE id = ?", (new_status, inquiry_id)
    )
    conn.commit()
    conn.close()
    flash("Inquiry status updated.", "success")
    return redirect(url_for("admin_inquiries"))


@app.route("/admin/pages/delivery", methods=["GET", "POST"])
@login_required
def admin_delivery_page():
    if request.method == "POST":
        return save_delivery_page()
    page = fetch_page("delivery")
    if page:
        while len(page["steps"]) < 3:
            page["steps"].append({"title": "", "body": ""})
        while len(page["blocks"]) < 4:
            page["blocks"].append({"title": "", "body": "", "image": "", "layout": "left"})
    return render_template("admin/delivery_page.html", page=page)


@app.route("/admin/pages")
@login_required
def admin_pages():
    conn = get_db()
    rows = conn.execute(
        "SELECT slug, title FROM pages WHERE slug != 'delivery' ORDER BY title"
    ).fetchall()
    conn.close()
    return render_template("admin/pages_list.html", pages=rows)


@app.route("/admin/pages/<slug>", methods=["GET", "POST"])
@login_required
def admin_page_edit(slug):
    if slug == "delivery":
        return redirect(url_for("admin_delivery_page"))
    if request.method == "POST":
        return save_generic_page(slug)
    page = fetch_page(slug)
    if not page:
        abort(404)
    while len(page["blocks"]) < 4:
        page["blocks"].append({"title": "", "body": "", "image": "", "layout": "left"})
    return render_template("admin/page_form.html", page=page)


@app.route("/admin/blog")
@login_required
def admin_blog():
    posts = fetch_blog_posts(published_only=False)
    return render_template("admin/blog_list.html", posts=posts)


@app.route("/admin/blog/new", methods=["GET", "POST"])
@login_required
def admin_blog_new():
    if request.method == "POST":
        return save_blog_post()
    return render_template("admin/blog_form.html", post=None, mode="new")


@app.route("/admin/blog/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def admin_blog_edit(post_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM blog_posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    if not row:
        abort(404)
    post = dict(row)
    if request.method == "POST":
        return save_blog_post(post_id)
    return render_template("admin/blog_form.html", post=post, mode="edit")


@app.route("/admin/blog/<int:post_id>/delete", methods=["POST"])
@login_required
def admin_blog_delete(post_id):
    conn = get_db()
    conn.execute("DELETE FROM blog_posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    flash("Blog post deleted.", "success")
    return redirect(url_for("admin_blog"))

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
